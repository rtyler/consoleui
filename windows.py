import curses
import os
import sys

import consoleui
import consoleui.events


class OpenFileDialog(consoleui.Window):
	def __init__(self, *args, **kwargs):
		super(OpenFileDialog, self).__init__(*args, **kwargs)

		self.callback = kwargs['callback']
		self.start = kwargs.get('start')

		self.parent = consoleui.root_window
		self.cwindow = self.parent.centered_subwindow(window=self)

		self.cwindow.keypad(1)

		self.cwd = self.start or os.getcwd()

		self.listing = os.listdir(self.cwd)
		self.selected = 0
		self.offset = 0
		self.current_max = 0
		self.more = False

	def keyhandler(self, key):
		if key == curses.KEY_DOWN:
			self.selected = self.selected + 1
			self.redraw(nofullrefresh=True)
			return True
		if key == curses.KEY_UP and self.selected != 0:
			self.selected = self.selected - 1
			self.redraw(nofullrefresh=True)
			return True

		if key == 10:
			listing = self.dir_listing()
			selected = listing[self.selected]
			path = '%s%s%s' % (self.cwd, os.path.sep, selected)

			if os.path.isdir(path):
				self.cwd = path
				self.selected = 0
				self.redraw(nofullrefresh=True)
				return True
			else:
				self.callback(path)
				return None
		return True

	def dir_listing(self):
		listing = os.listdir(self.cwd)
		listing.sort()
		listing.insert(0, '..')
		return listing

	def render(self):
		self.cwindow.bkgdset(0, curses.A_REVERSE)
		self.box()
		self.fill_window(self.cwindow)
		self.cwindow.addstr(1, 2, 'OPEN FILE', curses.A_BOLD | curses.A_UNDERLINE)
		maxy, maxx = self.cwindow.getmaxyx()
		bottom = (maxy - 5)

		listing = self.dir_listing()

		if self.selected >= bottom - 1:
			if self.selected > self.current_max:
				if not self.selected == len(listing):
					self.offset = self.offset + 1
			else:
				self.offset = self.offset - 1
		if self.selected < self.offset:
			self.offset = self.selected
		trimmed = listing[self.offset:(bottom + self.offset)]
		self.current_max = self.selected
		self.more = (len(listing) > bottom) and not (len(trimmed) < len(listing[:bottom]))

		starty, startx = 3, 3 
		for i in xrange(len(trimmed)):
			entry = trimmed[i]
			if entry == listing[self.selected]:
				self.cwindow.addstr(starty, startx + 1, '>> %s' % entry, curses.A_BOLD)
			else:
				self.cwindow.addstr(starty, startx, entry)
			starty = starty + 1
		if self.more:
			self.cwindow.addstr(starty, startx, 'more..', curses.A_BOLD | curses.A_UNDERLINE)

	def redraw(self, **kwargs):
		self.render()
		if not kwargs.get('nofullrefresh'):
			self.parent.redraw()

		
def OpenFilePlease(start, callback):
	dialog = OpenFileDialog(start=start, callback=callback)
	dialog.render()
	dialog.focus()
	
