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

	def close(self):
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
			self.run = False # Fall through for now
		self.close()



