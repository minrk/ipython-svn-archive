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
			self.factoryList = factory
		else:
			self.factoryList = [factory]
		for f in self.factoryList:
			f.service = self
		if type(engine) is list:
			self.engineList = engine
		else:
			self.engineList = [engine]
		for e in self.engineList:
			e.service = self
	
	def setId(self, id):
		self.id = id
	
	def setFactoryList(self, factoryList):
		for f in self.factoryList:
			del f
		self.factoryList = factoryList
		for f in factoryList:
			f.service = self
	
	def addFactory(self, factory):
		if type(factory) is list:
			self.factoryList.extend(factory)
			for f in factory:
				f.service = self
		else:
			self.factoryList.append(factory)
			factory.service = self
	
	def addEngine(self, engine=None):
		if not engine:
			engine = Engine()


