'''
	consoleui is an event-driven UI toolkit for curses. 

	The general idea is to provide a manageable set of widgets in an
	object oriented fashion to where the end-user (application developer)
	doesn't have to muck about with curses just to get a reasonable
	console-based interface


	Author(s)
		* R. Tyler Ballance <tyler@monkeypox.org>
'''
import curses
import sys
import weakref


from consoleui import events
from consoleui import errors
from consoleui import util

class AbstractWidget(object):
	'''
		AbstractWidget is the base class for all cosnoleui controls 
	'''
	def __init__(self, *args, **kwargs):
		self.children = []
		self.parent = None
		self.has_focus = False
		self.propogate_redraws = True
		events.manager.observe(events.Standard.Closing, self.watch_closes)

	def redraw(self):
		if self.propogate_redraws:
			for child in self.children:
				child.redraw()

	def render(self):
		if self.propogate_redraws:
			for child in self.children:
				child.render()

	def close(self):
		for child in self.children:
			child.close()
		events.manager.fire(events.Standard.Closing, widget=self)
		if self.parent:
			self.parent.redraw()

	def handle_input(self, keycode):
		return True

	def watch_closes(self, event_name, **eventkwargs):
		widget = eventkwargs.get('widget')
		if widget:
			self.children = [c for c in self.children if not c == widget]

	def addchild(self, widget, focus):
		if not isinstance(widget, AbstractWidget):
			raise errors.InvalidArgumentError('AbstractWidget.addchild(widget) only accepts instantiated AbstractWidget subclasses')
		if focus:
			for child in self.children:
				child.has_focus = False

		self.children.append(widget)
		widget.parent = weakref.proxy(self)
		widget.has_focus = focus
		return True

class RootWindow(AbstractWidget):
	exit_keys = [util.Keys.ESCAPE, ord('q'), ord('Q')]

	def __init__(self, *args, **kwargs):
		super(RootWindow, self).__init__(*args, **kwargs)
		self.title = kwargs['name']
		self.ceiling = 0 # Y-coordinate where usable space starts below title bar
		self.run = True # Continue event_loop
		self.echo = False # Echo characters on input

		self._cwin = curses.initscr()
		self._cwin.keypad(1)

		self.y, self.x = self._cwin.getmaxyx()

		self._install_colors()

		events.manager.observe(events.Standard.Quit, self.close)

	def _install_colors(self):
		curses.start_color()
		curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
		curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
		curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_RED)
		curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)

	def render(self):
		self._cwin.bkgdset(0, curses.A_NORMAL) # Reset background color
		self._cwin.erase()
		self._cwin.refresh()
		self.y, self.x = self._cwin.getmaxyx()
		util.UI.draw_padded_line(self._cwin, 0, 0, self.title, curses.A_BOLD | curses.color_pair(1))
		util.UI.draw_hline(self._cwin, 1, 0)
		self.ceiling = 2
		super(RootWindow, self).render()

	def redraw(self):
		self.propogate_redraws = False
		self.render()
		self.propogate_redraws = True
		super(RootWindow, self).redraw()

	def close(self, *args, **kwargs):
		super(RootWindow, self).close()

		curses.echo()
		curses.nocbreak()
		curses.endwin()

	def event_loop(self):
		while self.run:
			if self.echo:
				curses.echo()
			else:
				curses.noecho()
			keycode = self._cwin.getch()
			if keycode == curses.KEY_RESIZE:
				self.redraw()
				continue
			if keycode in self.exit_keys:
				self.run = False
				events.manager.fire(events.Standard.Exiting)
				continue

			for child in self.children:
				if not child.has_focus:
					continue
				self.run = child.handle_input(keycode)
				if isinstance(self.run, list):
					self.run = [r for r in self.run if r]
		self.close()

class RootMenu(AbstractWidget):
	separator = '  |  '
	HOTKEY = curses.A_BOLD | curses.A_UNDERLINE

	def __init__(self, *args, **kwargs):
		super(RootMenu, self).__init__(*args, **kwargs)
		self.elements = kwargs['elements']
		self.keys = {}
		self.y, self.x = 1, 1

	def redraw(self):
		super(RootMenu, self).redraw()
		self.render()

	def render(self):
		assert self.parent, ('RootMenu cannot have a parent set to None in order to render!')
		x, y = 1, self.parent.ceiling 
		window = self.parent._cwin
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
				window.addstr(y, x, item[under+2:], curses.A_NORMAL)
				x = x + len(item[under+2:])
			else:
				window.addstr(y, x, item, curses.A_NORMAL)
				x = x + len(item)

			if element != self.elements[-1]:
				window.addstr(y, x, self.separator, curses.A_NORMAL)
				x = x + len(self.separator)
		util.UI.draw_hline(window, 3, 0)

	def handle_input(self, keycode):
		try:
			keych = chr(keycode)
			if self.keys.get(keych):
				return events.manager.fire(self.keys[keych], widget=weakref.proxy(self))
		except ValueError:
			pass
		return True


class Scrollable(AbstractWidget):
	pass

class ScrollableTextView(Scrollable):
	def __init__(self, *args, **kwargs):
		super(ScrollableTextView, self).__init__(*args, **kwargs)

		self.lines = kwargs['lines']
		self.wordwrap = kwargs.get('wordwrap')
		self.height = len(self.lines) + 2
		self.width = 0
		for line in self.lines:
			if len(line) > self.width:
				self.width = len(line)

		self.width = self.width + 5
		self._cpad = None
		self._minrow = 0
		self._maxrow = 0


	def render(self):
		parenty, parentx = self.parent._cwin.getmaxyx()
		if self.wordwrap:
			self.width = parentx
			self.height = parenty * 2
		self._maxrow = parenty
		if not self._cpad:
			self._cpad = curses.newpad(self.height, self.width)
			y = 0 
			for line in self.lines:
				if not self.wordwrap:
					util.UI.draw_padded_line(self._cpad, i, 0, line)
				else:
					chunks = line.split(' ')
					x = 0
					length = 0
					for chunk in chunks:
						if (length + len(chunk) + 1) > self.width:
							y = y + 1
							x = 0
							length = 0
						util.UI.draw_padded_line(self._cpad, y, x, '%s ' % chunk)
						bump = (len(chunk) + 1)
						length = length + bump
						x = x + bump
				y = y + 1
		
		self._cpad.refresh(0, 0, self._minrow, 0, self._maxrow - 1, self.width)

		super(ScrollableTextView, self).render()

