"""The engine service
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.application import service

class EngineService(service.Service):
	"""template service for controller service pair listenUp, listenDown"""
	def __init__(self, id=None, factory=[]):
		self.id = id
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
	
	def set_id(self, id):
		self.id = id
	
	def set_factory_list(self, factory_list):
		for f in self.factory_list:
			del f
		self.factory_list = factory_list
		for f in factory_list:
			f.service = self
	
	def add_factory(self, factory):
		if type(factory) is list:
			self.factory_list.extend(factory)
			for f in factory:
				f.service = self
		else:
			self.factory_list.append(factory)
			factory.service = self
	
	def add_engine(self, engine=None):
		if not engine:
			engine = Engine()


