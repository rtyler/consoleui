'''
	util - grab bag
'''

import curses

class Keys(object):
	ESCAPE = 27 # curses doesn't define a KEY_ESCAPE for some reason

class UI(object):
	@staticmethod
	def draw_padded_line(window, y, x, line, attrs=0):
		winy, winx = window.getmaxyx()
		window.addstr(y, x, '%s%s' % (line, ''.join([' ' for x in xrange( (winx - len(line) - x - 1) )])), attrs)

	@staticmethod
	def draw_hline(window, y, x):
		winy, winx = window.getmaxyx()
		window.hline(y, x, curses.ACS_HLINE, (winx - x - 1))
