'''
	dialogs - collection of useful dialogs
'''
import curses

import consoleui

from consoleui import events
from consoleui import util

class ModalDialog(consoleui.AbstractWidget):
	def __init__(self, *args, **kwargs):
		super(ModalDialog, self).__init__(*args, **kwargs)

		self.parent = kwargs['parent']
		self.message = kwargs['message']
		self.okay = kwargs.get('okay')
		self.cancel = kwargs.get('cancel')
		assert isinstance(self.parent, consoleui.RootWindow), (self.parent, 'ModalDialog can only be attached to the RootWindow')
		self._derived_cwin = None

		self.width = 90 # cols
		self.height = 15 # rows

	def render(self):
		py, px = self.parent._cwin.getmaxyx()
		begin_y = int(py / 2.0) - int(self.height / 2.0)
		begin_x = int(px / 2.0) - int(self.width / 2.0)
		self._derived_cwin = self.parent._cwin.derwin(self.height, self.width, begin_y, begin_x)
		self._derived_cwin.box()

		center = int(self.width / 2.0)
		title = 'ALERT'
		util.UI.draw_padded_line(self._derived_cwin, 1, (center - int(len(title) / 2.0)), title, curses.A_BOLD)
		util.UI.draw_hline(self._derived_cwin, 2, 0)
		self._derived_cwin.refresh()

	def close(self):
		if self._derived_cwin:
			self._derived_cwin.erase()
			self._derived_cwin.refresh()
			self.parent.redraw()
		super(ModalDialog, self).close()


