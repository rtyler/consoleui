import types

class StandardEvents(object):
	QuitApplication = 'ConsoleUIQuit'
	CloseWIndow = 'ConsoleUICloseWindow'

class EventManagerError(Exception):
	pass

class EventManager(object):
	def __init__(self, *args, **kwargs):
		self.name = kwargs['name']
		self.observers = {}

	def register_handler(self, event, handler):
		if not isinstance(handler, types.MethodType) or not isinstance(handler, types.FunctionType):
			raise EventManagerError('When using register_handler(event, handler) the handler argument must be a method or function')
		if not self.observers.get(event):
			self.observers[event] = []
		self.observers[event].append(handler)

	def raise_event(self, event, **kwargs):
		if self.observers.get(event):
			for handler in self.observers[event]:
				handler(event, **kwargs)
	
manager = EventManager(name='Global Event Manager')
