#!/usr/bin/env python

import consoleui


def main():
	rwin = consoleui.RootWindow(name='Hello World')
	rwin.render()
	rwin.event_loop()

if __name__ == '__main__':
	main()
