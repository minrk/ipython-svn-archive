"""The Controller Service
Classes - 
	Engine - an object for use in the Controller service to keep track of 
			properties of each engine connected to the controller
	ControllerService - the Controller service itself
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.application import internet, service

class Engine(object):
	"""Engine object existing inside controller service"""
	def __init__(self, service=None, id=None, addr=(), protocol_instance=None, qic):
		self.service = service
		self.id = id
		self.addr = addr
		self.protocol_instance = protocol_instance

class ControllerService(service.Service):
	"""template service for controller service pair listenUp, listenDown"""
	def __init__(self, name='ControllerService', factory=[], engine=[]):
		self.SetName(name)
		if type(factory) is list:
			self.factory_list = factory
		else:
			self.factory_list = [factory]
		for f in self.factory_list:
			f.service = self
		if type(engine) is list:
			self.engine_list = engine
		else:
			self.engine_list = [engine]
		for e in self.engine_list:
			e.service = self
	
	
	def set_factory_list(self, factory_list):
		for f in self.factory_list:
			del f
		self.factory_list = factory_list
		for f in factory_list:
			f.service = self
	
	def add_f(self, factory):
		if type(factory) is list:
			self.factory_list.extend(factory)
			for f in factory:
				f.service = self
		else:
			self.factory_list.append(factory)
			factory.service = self
	
	def addEngine(self, engine=None):
		if not engine:
			engine = Engine(self)


