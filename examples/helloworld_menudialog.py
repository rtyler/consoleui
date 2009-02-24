#!/usr/bin/env python

import consoleui
import consoleui.dialogs

def _aboutmenu_handler(event_name, **eventkwargs):
	widget = eventkwargs['widget']
	dialog = consoleui.dialogs.ModalDialog(parent=widget.parent, message='Helllooo World!')
	widget.parent.addchild(dialog, False)
	dialog.render()
	return True

def _exitmenu_handler(event_name, **eventkwargs):
	consoleui.events.manager.fire(consoleui.events.Standard.Quit)

def main():
	rwin = consoleui.RootWindow(name='Hello World with a Menu!')
	menu_elements = [('_About', 'ABOUT_MENU'), ('_Exit', 'EXIT_MENU')]
	rmenu = consoleui.RootMenu(elements=menu_elements)
	rwin.addchild(rmenu, True) # Focus

	consoleui.events.manager.observe('ABOUT_MENU', _aboutmenu_handler)
	consoleui.events.manager.observe('EXIT_MENU', _exitmenu_handler)

	rwin.render()
	rwin.event_loop()

if __name__ == '__main__':
	main()
