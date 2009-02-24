#!/usr/bin/env python
import os
import sys

import consoleui


def main():
	fd = open('examples/sampletext.txt', 'r')
	lines = fd.readlines()
	fd.close()
	rwin = consoleui.RootWindow(name='Hello Scrolling!')
	textview = consoleui.ScrollableTextView(lines=lines, wordwrap=True)
	rwin.addchild(textview, True)
	rwin.render()
	rwin.event_loop()

if __name__ == '__main__':
	main()
