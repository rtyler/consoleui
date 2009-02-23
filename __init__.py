import copy
import curses
import sys
import weakref

import consoleui.errors
import consoleui.events

class Keys(object):
	ESCAPE = 27 # curses doesn't define a KEY_ESCAPE for some reason

focus_stack = []
root_window = None

class Widget(object):
	'''
		Abstract base class for all ConsoleUI classes
	'''
	def __init__(self, *args, **kwargs):
		super(Widget, self).__init__(*args, **kwargs)
		self.children = []
		self.parent = kwargs.get('parent')

	def render(self):
		raise consoleui.errors.AbstractError('render() should be defined in the class subclassing Widget')

	def focus(self):
		curses.noecho()
		global focus_stack
		focus_stack.append(weakref.proxy(self))

	def unfocus(self):
		# Widget.close() will handle adjusting the focus_stack, unfocus will simply focus the next lower Widget
		global focus_stack
		if len(focus_stack):
			focus_stack[-1].redraw()
			focus_stack[-1].focus()

	def close(self):
		global focus_stack
		focus_stack.pop()

	def redraw(self):
		pass

	def minimize(self):
		pass

	def draw_padded_line(self, window, y, x, line, attrs=0):
		winy, winx = window.getmaxyx()
		window.addstr(y, x, '%s%s' % (line, ''.join([' ' for x in xrange( (winx - len(line) - x - 1) )])), attrs)

	def draw_hline(self, window, y, x):
		winy, winx = window.getmaxyx()
		window.hline(y, x, curses.ACS_HLINE, (winx - x - 1))

class Menu(Widget):
	''' 
		Menu is the base class for rendering a horizontal menu
	'''
	separator = '  |  '
	HOTKEY = curses.A_BOLD | curses.A_UNDERLINE 
	NORMAL = curses.A_NORMAL
	def __init__(self, *args, **kwargs):
		super(Menu, self).__init__(*args, **kwargs)
		self.elements = kwargs['elements']
		self.keys = {}
		self.x = 1
		self.y = 1

	def curses_window(self):
		return self.parent.curses_window()
	
	def getyx(self):
		return (self.y, self.x)

	def render(self):
		assert self.parent, ('Parent cannot be None to render a Menu!')
		x, y = 1, 3
		window = self.parent.curses_window()
		for element in self.elements:
			item, event = element
			under = None
			try:
				under = item.index('_')
			except ValueError:
				pass

			if not under == None:
				action_key = item[under+1:under+2]
				self.keys[action_key] = event
				window.addstr(y, x, action_key, self.HOTKEY)
				x = x + 1
				window.addstr(y, x, item[under+2:], self.NORMAL)
				x = x + len(item[under+2:])
			else:
				window.addstr(y, x, item, self.NORMAL)
				x = x + len(item)

			if element != self.elements[-1]:
				window.addstr(y, x, self.separator, self.NORMAL)
				x = x + len(self.separator)

	def redraw(self):
		self.parent.redraw()

	def focus(self):
		super(Menu, self).focus()
		key = True
		window = self.parent.curses_window()
		while key:
			key = window.getch()
			if key == curses.KEY_RESIZE:
				self.redraw()
				continue
			try:
				keych = chr(key)
				if self.keys.get(keych):
					consoleui.events.manager.fire(self.keys[keych])
			except ValueError:
				pass

class Submenu(Widget):
	''' Submenu is a basic class for handling vertically drawn, i.e. sub-menus '''
	HOTKEY = curses.A_BOLD | curses.A_UNDERLINE 
	NORMAL = curses.A_NORMAL
	def __init__(self, *args, **kwargs):
		super(Submenu, self).__init__(*args, **kwargs)
		self.elements = kwargs['elements']
		self._window = None
		self._width = 0
		self.keys = {}

	def render(self):
		assert self.parent, ('Parent cannot be None to render a submenu!')
		assert isinstance(self.parent, Menu), (self.parent, 'Expecting parent widget to be a Menu')
		
		elms = copy.deepcopy(self.elements)
		elms.sort(key=lambda e: len(e[0]), reverse=True)
		self._width = len(elms[0][0]) + 1
	
		parenty, parentx = self.parent.getyx()
		self._window = self.parent.curses_window().derwin( 5 + len(self.elements), 50, parenty, parentx)

		x, y  = parentx + 1, parenty + 2
		for element in self.elements:
			x = 1
			y = y + 1
			item, event = element
			under = None
			try:
				under = item.index('_')
			except ValueError:
				pass

			if item == '---':
				self._window.hline(y, x, curses.ACS_HLINE, self._width)
				continue

			if not under == None:
				action_key = item[under+1:under+2]
				self.keys[action_key] = event
				self._window.addstr(y, x, action_key, self.HOTKEY)
				x = x + 1
				self._window.addstr(y, x, item[under+2:], self.NORMAL)
			else:
				self._window.addstr(y, x, item, self.NORMAL)
			self._window.refresh()
	
	def redraw(self):
		self.render()
		self.parent.redraw()

	def close(self):
		self._window.erase()
		self._window.refresh()
		self.parent.redraw()
		global focus_stack
		super(Submenu, self).close()

	def unfocus(self):
		self.close()
		super(Submenu, self).unfocus()
	
	def focus(self):
		super(Submenu, self).focus()
		key = True
		while key:
			key = self._window.getch()
			if key == curses.KEY_RESIZE:
				self.redraw()
				continue
			if key == Keys.ESCAPE:
				return self.unfocus()
			keych = chr(key)
			if self.keys.get(keych):
				consoleui.events.manager.fire(self.keys[keych])

class Window(Widget):
	def __init__(self, *args, **kwargs):
		super(Window, self).__init__(*args, **kwargs)
		self.cwindow = kwargs.get('cwindow')
		self.boxed = False
		if not hasattr(self, 'keyhandler'):
			self.keyhandler = None

	def curses_window(self):
		return self.cwindow

	def box(self):
		self.boxed = True
		self.cwindow.box()

	def render(self):
		pass

	def redraw(self):
		pass

	def close(self):
		self.curses_window().erase()
		self.curses_window().refresh()
		super(Window, self).close()

	def fill_window(self, window, boxed=False):
		winy, winx = window.getmaxyx()
		for i in xrange(winy):
			if boxed and i == 0 or i == (winy - 1):
				continue
			self.draw_padded_line(window, i, 1, '')
	

	def focus(self):
		super(Window, self).focus()
		key = True
		while key:
			key = self.cwindow.getch()
			if key == curses.KEY_RESIZE:
				self.redraw()
				continue
			if key == Keys.ESCAPE:
				self.close()
				return self.unfocus()
			if self.keyhandler:
				key = self.keyhandler(key)
		self.unfocus()

class RootWindow(Window):
	def __init__(self, *args, **kwargs):
		global root_window
		assert root_window == None, ('Cannot run two RootWindow objects at once!')
		kwargs['cwindow'] = curses.initscr()
		root_window = self
		self.menu = None

		super(RootWindow, self).__init__(*args, **kwargs)

		self.title = kwargs['title']
		self.title_attrs = kwargs.get('title_attrs') or 0
		self.ceiling = 0 # Y-coordinate where usable space starts below title bar

		self.y, self.x = self.cwindow.getmaxyx()

		self.install_colors()

		self.title_attrs = self.title_attrs | curses.color_pair(1)
		self.cwindow.keypad(1)

	def install_colors(self):
		curses.start_color()
		curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
		curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
		curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_RED)
		curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)


	def render(self):
		self.cwindow.bkgdset(0, curses.A_NORMAL)
		self.cwindow.erase()
		self.cwindow.refresh()
		self.y, self.x = self.cwindow.getmaxyx()
		self.draw_padded_line(self.cwindow, 1, 0, self.title, attrs=self.title_attrs)
		self.cwindow.hline(2, 0, curses.ACS_HLINE, self.x)
		self.cwindow.hline(4, 0, curses.ACS_HLINE, self.x)
		self.ceiling = 5

	def redraw(self):
		self.render()
		if self.menu:
			self.menu.render()
		self.cwindow.refresh()

	def focus(self):
		# If I receive focus, and I have a menu, I'll pass it along
		if self.menu:
			self.menu.focus()

	def centered_subwindow(self, window=None):
		cwin = curses.newwin( (self.y - self.ceiling - 1), (self.x - 2), self.ceiling + 1, 1 )
		if window:
			return cwin
		window = Window(cwindow=cwin)
		return window

