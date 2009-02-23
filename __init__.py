import copy
import curses
import weakref

import consoleui.errors

class Keys(object):
	ESCAPE = 27 # curses doesn't define a KEY_ESCAPE for some reason

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

	def render(self):
		assert self.parent, ('Parent cannot be None to render a Menu!')
		x, y = 1, 3
		for element in self.elements:
			under = None
			try:
				under = element.index('_')
			except ValueError:
				pass

			if not under == None:
				self.parent.addstr(y, x, element[under+1:under+2], self.HOTKEY)
				x = x + 1
				self.parent.addstr(y, x, element[under+2:], self.NORMAL)
				x = x + len(element[under+2:])
			else:
				self.parent.addstr(y, x, element, self.NORMAL)
				x = x + len(element)

			if element != self.elements[-1]:
				self.parent.addstr(y, x, self.separator, self.NORMAL)
				x = x + len(self.separator)

class Window(Widget):
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

	def render(self):
		assert self.parent, ('Parent cannot be None to render a submenu!')
		assert isinstance(self.parent, Menu), (self.parent, 'Expecting parent widget to be a Menu')
		startx, starty = 1, 3
		
		elms = copy.deepcopy(self.elements)
		elms.sort(key=lambda e: len(e), reverse=True)
		self._width = elms[0] + 1
		
		self._window = curses.newwin(len(self.elements), self._width, starty, startx)
	
		for element in self.elements:
			y = starty + 1
			x = startx
			under = None
			try:
				under = element.index('_')
			except ValueError:
				pass

			if not under == None:
				self._window.addstr(y, x, element[under+1:under+2], self.HOTKEY)
				x = x + 1
				self._window.addstr(y, x, element[under+2:], self.NORMAL)
			elif element == '---':
				self._window.hline(y, x, curses.ACS_HLINE, self._width)
			else:
				self._window.addstr(y, x, element, self.NORMAL)



