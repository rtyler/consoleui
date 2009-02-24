'''
	events - module containing standard consoleui events and the global event manager
'''

import types

from consoleui import errors

class EventManager(object):
	def __init__(self, *args, **kwargs):
		self.name = kwargs['name']
		self.observers = {}

	def observe(self, event_name, handler_func):
		if not isinstance(handler_func, types.MethodType) and not isinstance(handler_func, types.FunctionType):
			raise errors.InvalidArgumentError(('NotificationCenter.observe() requires a function', handler_func))
		if not self.observers.get(event_name):
			self.observers[event_name] = []
		self.observers[event_name].append(handler_func)

	def unobserve(self, event_name, handler_func):
		'''
			Remove handler_func from observing event_name

			Returns True on success, False on failure
		'''
		if not isinstance(handler_func, types.MethodType) and not isinstance(handler_func, types.FunctionType):
			raise errors.InvalidArgumentError(('NotificationCenter.observe() requires a function', handler_func))

		if not self.observers.get(event_name):
			return False

		stack = []
		rc = False
		for func in self.observers[event_name]:
			if func == handler_func:
				rc = True
				continue
			stack.append(func)
		self.observers[event_name] = stack
		return rc

	def fire(self, event_name, **eventargs):
		'''
			Fire the actual event, this will cause observers to execute serially 

			Returns a list of return values from observers
		'''
		rc = []
		if self.observers.get(event_name):
			for func in self.observers[event_name]:
				rc.append( func(event_name, **eventargs) )
		return rc

class Standard(object):
	GainFocus = 'consoleui.WidgetGainingFocus'
	LoseFOcus = 'consoleui.WidgetLosingFocus'

	Quit = 'consoleui.ApplicationQuit'
	Exiting = 'consoleui.ApplicationIsExiting'


manager = EventManager(name='Global Notification Center')
