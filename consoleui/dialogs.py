'''
	dialogs - collection of useful dialogs
'''
import curses
import curses.ascii

import consoleui

from consoleui import events
from consoleui import util

class ModalDialog(consoleui.AbstractWidget):
	def __init__(self, *args, **kwargs):
		super(ModalDialog, self).__init__(*args, **kwargs)

		self.parent = kwargs['parent']
		self.message = kwargs['message']
		self.okay = kwargs.get('okay')
		assert isinstance(self.parent, consoleui.RootWindow), (self.parent, 'ModalDialog can only be attached to the RootWindow')
		self._derived_cwin = None

		self.width = 50 # cols
		self.height = 12 # rows
		self.rendered = False
		

	def render(self):
		py, px = self.parent._cwin.getmaxyx()
		begin_y = int(py / 2.0) - int(self.height / 2.0)
		begin_x = int(px / 2.0) - int(self.width / 2.0)
		self._derived_cwin = self.parent._cwin.derwin(self.height, self.width, begin_y, begin_x)
		self._derived_cwin.box()

		center = int(self.width / 2.0)
		title = 'ALERT'
		util.UI.draw_padded_line(self._derived_cwin, 1, (center - int(len(title) / 2.0)), title, curses.A_BOLD)
		util.UI.draw_hline(self._derived_cwin, 2, 1)

		util.UI.draw_padded_line(self._derived_cwin, 4, (center - int(len(self.message) / 2.0)), self.message)

		self._button_cwin = self._derived_cwin.derwin(3, 10, (self.height - 5), (center - 5))
		self._button_cwin.box()
		util.UI.draw_padded_line(self._button_cwin, 1, 1, 'Okay', curses.A_BOLD | curses.A_REVERSE | curses.A_UNDERLINE)

		self._derived_cwin.refresh()
		self.has_focus = True # I'm Modal damnit!
		self.rendered = True

	def close(self):
		self.has_focus = True
		if self._derived_cwin:
			self._derived_cwin.erase()
			self._derived_cwin.refresh()
		super(ModalDialog, self).close()

	def handle_input(self, keycode):
		if not self.rendered:
			return True
		if keycode == curses.ascii.CR or keycode == curses.ascii.LF:
			rc = True
			self.close()
			if self.okay:
				rc = consoleui.events.fire(self.okay)
			return rc
		return True
