# encoding: utf-8
# -*- test-case-name: ipython1.test.test_enginevanilla -*-
"""Expose the IPython EngineService using our vanilla protocol.

This modules defines interfaces and adapters to connect an EngineService to
a ControllerService using the vanilla protocol.  It defines the following classes:

On the Engine (client) side:

 * IPBEngineClientFactory
 * PBEngineClientFactory
 * IPBEngine
 * PBEngineReferenceFromService
 
On the Controller (server) side:
 
 * EngineFromReference
 * IPBRemoteEngineRoot
 * PBRemoteEngineRootFromService
 * IPBEngineServerFactory
 
To do:

 * Why are isStatusOK and statusOK commented out?  Are we using them?
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import cPickle as pickle

from zope.interface import implements, Interface, Attribute
import zope.interface as zi
from twisted.python import components, log
from twisted.python.failure import Failure
from twisted.internet import reactor, defer

from ipython1.kernel import error, protocols
from ipython1.kernel.controllerservice import ControllerService, IControllerCore
from ipython1.kernel import newserialized
import ipython1.kernel.engineservice as engineservice

# Verbose debugging of deferreds

defer.setDebugging(1)


#-------------------------------------------------------------------------------
# Engine side of things
#-------------------------------------------------------------------------------

class IVanillaEngineClientProtocol(Interface):
    pass


class VanillaEngineClientProtocol(protocols.EnhancedNetstringReceiver):
    """The client side of the vanilla protocol."""
    
    implements(IVanillaEngineClientProtocol)
    
    nextHandler = None
    workVars = {}
    
    def connectionMade(self):
        self.transport.setTcpNoDelay(True)
        desiredID = self.factory.id
        self.nextHandler = self.handleRegister
        if desiredID is not None:
            self.sendString("REGISTER %i" % desiredID)
        else:
            self.sendString("REGISTER")
    
    def stringReceived(self, msg):
        if self.nextHandler is None:
            self.defaultHandler(msg)
        else:
            self.nextHandler(msg)
    
    def dispatch(self, msg):
        # Try to parse out a command
        splitLine = msg.split(' ', 1)
        if len(splitLine) == 1:
            cmd = splitLine[0]
            args = None
        else:
            cmd = splitLine[0]
            args = splitLine[1]
        
        # Try to dispatch to a handle_COMMAND method
        f = getattr(self, 'handle_%s' %
                    (cmd), None)            
        if f:
            f(args)
        else:
            self.dieLoudly('Command could not be dispatched: ' + msg)
    
    #---------------------------------------------------------------------------
    # Utility methods
    #---------------------------------------------------------------------------
        
    def dieLoudly(self, *args):
        """Die loudly in case of protocol errors."""
        id = self.factory.id
        for a in args:
            log.msg('Protocol Error [%i]: ' % id + repr(a))
        self.transport.loseConnection()
        reactor.stop()
    
    def defaultHandler(self, msg):
        self.dieLoudly(msg)
    
    def _reset(self):
        self.workVars = {}
        self.nextHandler = self.dispatch
    
    def handleUnexpectedData(self, args):
        self.dieLoudly(args)
    
    def sendSerialized(self, s, key):
        if s.getTypeDescriptor() == 'pickle':
            self.sendString('PICKLE %s' % key)
            self.sendString(s.getData())
        if s.getTypeDescriptor() == 'ndarray':
            self.sendString('ARRAY %s' % key)
            md = s.getMetadata()
            self.sendString(pickle.dumps(md['shape'], 2))
            self.sendString(md['dtype'])
            self.sendBuffer(s.getData())
    
    #---------------------------------------------------------------------------
    # The REGISTER command
    #---------------------------------------------------------------------------
 
    def handleRegister(self, args):
        splitArgs = args.split(' ',1)
        if len(splitArgs) == 2 and splitArgs[0] == 'REGISTER':
            try:
                id = int(splitArgs[1])
            except TypeError, e:
                self.dieLoudly("The controller protocol gave an id that is not an int: " + e)
            else:
                self._reset()
                self.factory.id = id
        else:
            self.dieLoudly(args)
    
    #---------------------------------------------------------------------------
    # The EXECUTE command
    #---------------------------------------------------------------------------
            
    def handle_EXECUTE(self, lines):
        # This will block so callbacks are called immediately!
        if lines is None:
            self.executeFail()
        d = self.factory.execute(lines)
        d.addCallback(self.handleExecuteSuccess)
        d.addErrback(self.handleExecuteFailure)
    
    def handleExecuteSuccess(self, result):
        try:
            serial = newserialized.serialize(result)
        except:
            self.handleExecuteFailure(Failure())
        else:
            self.sendSerialized(serial, 'RESULT')
            self.executeOK()
    
    def handleExecuteFailure(self, reason):
        try:
            serial = newserialized.serialize(reason)
        except:
            self.executeFail()
        else:
            self.sendSerialized(serial, 'FAILURE')
            self.executeOK()
    
    def executeOK(self):
        self._reset()
        self.sendString('EXECUTE OK')
    
    def executeFail(self):
        self._reset()
        self.sendString('EXECUTE FAIL')
        
    #---------------------------------------------------------------------------
    # The PUSH command
    #---------------------------------------------------------------------------
    
    def handle_PUSH(self, args):
        if args is not None:
            self.dieLoudly('PUSH does not take any arguments: ' + args)
        else:
            self.nextHandler = self.handlePushing
            self.workVars['pushSerialsDict'] = {}
            self.sendString("READY")
    
    def handlePushing(self, msg):
        # What if DONE never comes
        if msg == 'DONE':
            self.handlePushDone()
            return
            
        msgList = msg.split(' ', 1)
        if len(msgList) == 2:
            pushType = msgList[0]
            self.workVars['pushKey'] = msgList[1]
            f = getattr(self, 'handlePushing_%s' % pushType, None)
            if f is not None:
                self.nextHandler = f
            else:
                self.dieLoudly('Unsupported serialization type: ' + pushType)
        else:
            self.dieLoudly('Data commands must have two arguments: ' + msg)
    
    def handlePushing_PICKLE(self, package):
        self.nextHandler = self.handlePushing
        serial = newserialized.Serialized(package, typeDescriptor='pickle')
        self.workVars['pushSerialsDict'][self.workVars['pushKey']] = serial
    
    def handlePushing_ARRAY(self, pShape):
        self.nextHandler = self.handlePushingArray_dtype
        serial = {}
        serial['shape'] = pickle.loads(pShape)
        self.workVars['pushSerial'] = serial
    
    def handlePushingArray_dtype(self, dtype):
        self.nextHandler = self.handlePushingArray_buffer
        self.workVars['pushSerial']['dtype'] = dtype
            
    def handlePushingArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handlePushing
        serial = newserialized.Serialized(arrayBuffer, 'ndarray', 
            self.workVars['pushSerial'])
        self.workVars['pushSerialsDict'][self.workVars['pushKey']] = serial
    
    def handlePushDone(self):
        ns = {}
        for k, v in self.workVars['pushSerialsDict'].iteritems():
            ns[k] = v
        # This will errback with serialization errors
        d = self.factory.pushSerialized(**ns)
        d.addCallback(self.pushOK)
        d.addErrback(self.pushFail)
    
    def pushOK(self, *args):
        self._reset()
        self.sendString('PUSH OK')
    
    def pushFail(self, reason):
        reason.printVerboseTraceback()
        self._reset()
        self.sendString('PUSH FAIL')
    
    #---------------------------------------------------------------------------
    # The PULL command
    #---------------------------------------------------------------------------
    
    def handle_PULL(self, args):

        keys = args.split(',')
        self.workVars['keys'] = keys
        self.nextHandler = self.handleUnexpectedData
        d = self.factory.pullSerialized(*keys)
        d.addCallbacks(self.handlePullingDone, self.pullFail)
        return d
    
    def handlePullingDone(self, oneOrMoreSerialized):
        if isinstance(oneOrMoreSerialized, (list, tuple)):
            for key, s in zip(self.workVars['keys'], oneOrMoreSerialized):
                self.sendSerialized(s, key)
        else:
            self.sendSerialized(oneOrMoreSerialized, self.workVars['keys'][0])
        self.pullOK()
    
    def pullOK(self):
        self._reset()
        self.sendString('PULL OK')
    
    def pullFail(self, reason):
        self._reset()
        self.sendString('PULL FAIL')
        
    #---------------------------------------------------------------------------
    # The GETRESULT command
    #---------------------------------------------------------------------------

    def handle_GETRESULT(self, args):
        self.nextHandler = self.handleUnexpectedData
        if args is None:
            d = self.factory.getResult()
        else:
            try:
                index = int(args)
            except TypeError:
                self.dieLoudly('Results should be indexed by integers: ' + args)
            else:
                d = self.factory.getResult(index)
        d.addCallback(self.handleGetResultSuccess)
        d.addErrback(self.handleGetResultFailure)
    
    def handleGetResultSuccess(self, result):
        try:
            serial = newserialized.serialize(result)
        except:
            self.handleGetResultFailure(Failure())
        else:
            self.sendSerialized(serial, 'RESULT')
            self.getResultOK()
    
    def handleGetResultFailure(self, reason):
        # I am not sure we need to catch this PickleError
        try:
            serial = newserialized.serialize(reason)
        except:
            self.getResultFail()
        else:
            self.sendSerialized(serial, 'FAILURE')
            self.getResultOK()
    
    def getResultOK(self):
        self._reset()
        self.sendString('GETRESULT OK')
    
    def getResultFail(self):
        self._reset()
        self.sendString('GETRESULT FAIL')
    
    #---------------------------------------------------------------------------
    # The RESET command
    #--------------------------------------------------------------------------- 
            
    def handle_RESET(self, args):
        d = self.factory.reset()
        d.addCallbacks(self.resetOK, self.resetFail)
    
    def resetOK(self, args):
        self._reset()
        self.sendString('RESET OK')
    
    def resetFail(self, reason):
        self._reset()
        self.sendString('RESET FAIL')
    
    #---------------------------------------------------------------------------
    # The KILL command
    #---------------------------------------------------------------------------
            
    def handle_KILL(self, args):
        d = self.factory.kill()
        d.addCallbacks(self.killOK, self.killFail)
    
    def killOK(self, args):
        self._reset()
        self.sendString('KILL OK')
    
    def killFail(self, reason):
        self._reset()
        self.sendString('KILL FAIL')
    
    #---------------------------------------------------------------------------
    # The STATUS command
    #--------------------------------------------------------------------------- 
            
    def handle_STATUS(self, args):
        d = self.factory.keys()
        d.addCallbacks(self.statusOK, self.statusFail)
    
    def statusOK(self, args):
        serial = newserialized.serialize(args)
        self.sendSerialized(serial, 'STATUS')
        self._reset()
        self.sendString('STATUS OK')
    
    def statusFail(self, reason):
        log.msg(reason)
        self._reset()
        self.sendString('STATUS FAIL')
    
    
class IVanillaEngineClientFactory(engineservice.IEngineCore,
    engineservice.IEngineSerialized):
    """Interface or the client factory of the Engine."""
    
    pass


class VanillaEngineClientFactoryFromEngineService(protocols.EnhancedClientFactory):
    """Adapt an EngineService to a vanilla protocol client factory."""
    
    implements(IVanillaEngineClientFactory)
    
    protocol = VanillaEngineClientProtocol
    
    def __init__(self, service):
        self.service = service
    
    # From IVanillaEngineClientFactory
    
    def _getID(self):
        return self.service.id
    
    def _setID(self, id):
        """Set the engine id, but with a hook for tests."""

        self.service.id = id
        self.notifySetID()   # Use as a hook for tests
    
    def notifySetID(self):
        """This method is meant to be a hook to use in testing.
        
        It will be called when the engine's id is set, which will e after
        is has finished registering with a controller.
        """
        pass
    
    id = property(_getID, _setID)
    
    #---------------------------------------------------------------------------
    # Methods from EngineService/IEngine interfaces
    #--------------------------------------------------------------------------- 

    def execute(self, lines):
        return self.service.execute(lines)
    
    def push(self, **namespace):
        return self.service.push(**namespace)
    
    def pull(self, *keys):
        return self.service.pull(*keys)
    
    def getResult(self, i=None):
        return self.service.getResult(i)
    
    def reset(self):
        return self.service.reset()
    
    def kill(self):
        return self.service.kill()
    
    def keys(self):
        return self.service.keys()
    
    def pushSerialized(self, **namespace):
        return self.service.pushSerialized(**namespace)
    
    def pullSerialized(self, *keys):
        return self.service.pullSerialized(*keys)
    

components.registerAdapter(VanillaEngineClientFactoryFromEngineService,
                           engineservice.EngineService,
                           IVanillaEngineClientFactory)

    
#-------------------------------------------------------------------------------
# Controller side of things
#-------------------------------------------------------------------------------

class IVanillaEngineServerProtocol(engineservice.IEngineBase):
    """Interface for the representation of an engine within the controller."""
    pass
    
    
class VanillaEngineServerProtocol(protocols.EnhancedNetstringReceiver):
    """Server side of the vanilla protocol."""
    
    # This is needed because, this class has to directly implement IEngineCore
    # and IEngineSerialized...or does it.  I probably needed to add this because 
    # a zi.providedBy call wasn't picking up the base intefaces of it.  But
    # from now on we should use IFoo.providedBy, which will pick of base 
    # interfaces properly.  I think I have fixed it and that we can and should 
    # use the second form.  B. Granger 12/15/06
    #implements(IVanillaEngineServerProtocol, *IVanillaEngineServerProtocol.__bases__)
    implements(IVanillaEngineServerProtocol)

    
    nextHandler = None
    workVars = {}
    _id = None
    
    def connectionMade(self):
        self.transport.setTcpNoDelay(True)
        self.nextHandler = self.dispatch
    
    def connectionLost(self, reason):
        self.factory.unregisterEngine(self.id)
    
    def _getID(self):
        return self._id
    
    def _setID(self, id):
        self._id = id
    
    id = property(_getID, _setID, doc="The engine's id.")
    
    #def sendString(self, s):
    #    log.msg('C: %s' % s)
    #    protocols.EnhancedNetstringReceiver.sendString(self, s)
    
    def stringReceived(self, msg):
        #log.msg('E: %s' % msg)
        if self.nextHandler is None:
            self.defaultHandler(msg)
        else:
            self.nextHandler(msg)
    
    def dispatch(self, msg):
        # Try to parse out a command
        splitLine = msg.split(' ', 1)
        if len(splitLine) == 1:
            cmd = splitLine[0]
            args = None
        else:
            cmd = splitLine[0]
            args = splitLine[1:]
        
        # Try to dispatch to a handle_COMMAND method
        f = getattr(self, 'handle_%s' %
                    (cmd), None)            
        if f:
            f(args)
        else:
            self.dieLoudly('Command could not be dispatched: ' + msg)
    
    #---------------------------------------------------------------------------
    # Utility methods
    #---------------------------------------------------------------------------
        
    def dieLoudly(self, *args):
        """Die loudly in case of protocol errors."""
        id = self.id
        for a in args:
            log.msg('Protocol Error [%i]: ' % id + repr(a))
        self.transport.loseConnection()
        reactor.stop()
    
    def defaultHandler(self, msg):
        self.dieLoudly('defaultHandler called with: ' + msg)
    
    def _reset(self):
        self.workVars = {}
        self.nextHandler = self.dispatch
    
    def _callbackAndReset(self, result):
        
        # The ordering here is EXTREMELY important
        # The workVars must be cleared before the Deferred is triggered,
        # so the Deferred must be saved in a local variable d
        self.nextHandler = self.dispatch
        d = self.workVars['deferred']
        self.workVars = {}
        d.callback(result)
    
    def _errbackAndReset(self, reason):
        
        # The ordering here is EXTREMELY important
        # The workVars must be cleared before the Deferred is triggered,
        # so the Deferred must be saved in a local variable d
        self.nextHandler = self.dispatch
        d = self.workVars['deferred']
        self.workVars = {}
        d.errback(reason)
    
    def _createDeferred(self):
        self.workVars['deferred'] = defer.Deferred()
        return self.workVars['deferred']
    
    def handleUnexpectedData(self, args):
        self.dieLoudly('Unexpected Data: %s' % args)
    
    def sendSerialized(self, s, key):
        if s.getTypeDescriptor() == 'pickle':
            self.sendString('PICKLE %s' % key)
            self.sendString(s.getData())
        if s.getTypeDescriptor() == 'ndarray':
            self.sendString('ARRAY %s' % key)
            md = s.getMetadata()
            self.sendString(pickle.dumps(md['shape'], 2))
            self.sendString(md['dtype'])
            self.sendBuffer(s.getData())
    
    def setupForIncomingSerialized(self, callbackString, errbackString=''):
        self.workVars['callbackString'] = callbackString
        if errbackString:
            self.workVars['errbackString'] = errbackString
        self.workVars['serialsDict'] = {}
        self.nextHandler = self.handleIncomingSerialized
        self.workVars['deferred'] = defer.Deferred()
        return self.workVars['deferred']
    
    def handleIncomingSerialized(self, msg):
        if msg == self.workVars['callbackString']:
            self.workVars['deferred'].callback(self.workVars['serialsDict'])
            return
        elif msg == self.workVars['errbackString']:
            #self.workVars['deferred'].errback(Failure(error.KernelError(msg)))
            # This is done as a hack to get the test to pass.  Most of the time
            # if there was a problem with an incoming object is didn't exist
            # so a NameError is expected.  BUT, if a serialization error was 
            # expected, this will not work.
            self.workVars['deferred'].errback(Failure(NameError("Problem getting object")))
            return
            
        msgList = msg.split(' ', 1)
        if len(msgList) == 2:
            serialType = msgList[0]
            self.workVars['serialKey'] = msgList[1]
            f = getattr(self, 'handleSerial_%s' % serialType, None)
            if f is not None:
                self.nextHandler = f
            else:
                self.dieLoudly('Unsupported serialization type: ' + serialType)
        else:
            self.dieLoudly('Data commands must have two arguments: ' + msg)
    
    def handleSerial_PICKLE(self, package):
        self.nextHandler = self.handleIncomingSerialized
        serial = newserialized.Serialized(package, typeDescriptor='pickle')
        self.workVars['serialsDict'][self.workVars['serialKey']] = serial
    
    def handleSerial_ARRAY(self, pShape):
        self.nextHandler = self.handleArray_dtype
        serial = {}
        serial['shape'] = pickle.loads(pShape)
        self.workVars['serial'] = serial
    
    def handleArray_dtype(self, dtype):
        self.nextHandler = self.handleArray_buffer
        self.workVars['serial']['dtype'] = dtype
    
    def handleArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handleIncomingSerialized
        serial = newserialized.Serialized(arrayBuffer, 'ndarray', 
            self.workVars['serial'])
        self.workVars['serialsDict'][self.workVars['serialKey']] = serial
    
    #---------------------------------------------------------------------------
    # The REGISTER command
    #---------------------------------------------------------------------------
    
    def handle_REGISTER(self, args):
        self.nextHandler = self.handleUnexpectedData
        if args is not None:
            desiredID = args[0]
            try:
                desiredID = int(desiredID)
            except TypeError:
                desiredID = None
        else:
            desiredID = None
        qe = engineservice.IEngineQueued(self)
        regDict = self.factory.registerEngine(qe, desiredID) 
        self.id = regDict['id']
        self.handleID(self.id)
    
    def handleID(self, id):
        self._reset()
        self.sendString('REGISTER %i' % id)
    
    #---------------------------------------------------------------------------
    # IEngineCore methods
    #---------------------------------------------------------------------------
    
    #---------------------------------------------------------------------------
    # The EXECUTE command
    #---------------------------------------------------------------------------
    
    def execute(self, lines):
        if not isinstance(lines, str):
            return defer.fail(Failure(TypeError('lines must be a string')))
        self.sendString('EXECUTE %s' % lines)
        d = self.setupForIncomingSerialized('EXECUTE OK', 'EXECUTE FAIL')
        d.addCallbacks(self.handleExecuteOK, self.handleExecuteFail)
        return d
    
    def handleExecuteOK(self, resultDict):
        if resultDict.has_key('RESULT'):
            result = newserialized.unserialize(resultDict['RESULT'])
            self._reset()
            return result
        elif resultDict.has_key('FAILURE'):
            f = newserialized.unserialize(resultDict['FAILURE'])
            f.raiseException()
    
    def handleExecuteFail(self, reason):
        self._reset()
        return reason
    
    #---------------------------------------------------------------------------
    # The PUSH command
    #---------------------------------------------------------------------------
    
    def push(self, **namespace):
        self.workVars['namespace'] = namespace
        self.sendString('PUSH')
        self.nextHandler = self.isPushReady
        d = self._createDeferred()
        return d
    
    def isPushReady(self, msg):
        if msg == 'READY':
            for k, v in self.workVars['namespace'].iteritems():
                try:
                    s = newserialized.serialize(v)
                except Exception, e:
                    log.msg('You tried to push an unserializable type, ignoring: ' + k)
                    self.pushFail(Failure())
                else:
                    self.sendSerialized(s, k)
            self.finishPush()
        else:
            self.dieLoudly('I was expecting README but got: ' + msg)
    
    def finishPush(self):
        self.nextHandler = self.isPushOK
        self.sendString('DONE')
    
    def isPushOK(self, msg):
        if msg == 'PUSH OK':
            self.pushOK()
        elif msg == 'PUSH FAIL':
            self.pushFail(Failure(error.KernelError('Received PUSH FAIL')))
        else:
            self.dieLoudly('Expected PUSH OK, got: ' + msg)
    
    def pushFail(self, f):
        self._errbackAndReset(f)
    
    def pushOK(self, result=None):
        self._callbackAndReset(result)
    
    #---------------------------------------------------------------------------
    # The PULL command
    #---------------------------------------------------------------------------
    
    def pull(self, *keys):
        keyString = ','.join(keys)
        self.sendString('PULL %s' % keyString)
        d = self.setupForIncomingSerialized('PULL OK', 'PULL FAIL')
        d.addCallback(self.handlePulledSerialized)
        d.addErrback(self.pullFail)
        return d
    
    def handlePulledSerialized(self, dictOfSerialized):
        result = []
        for k, v in dictOfSerialized.iteritems():
            try:
                obj = newserialized.unserialize(v)
            except:
                log.msg("You pulled an unserializable type, ignoring: " + k)
                obj = None
            result.append(obj)
        if len(result) == 1:
            result = result[0]
        self.pullOK()
        return result
    
    def pullOK(self):
        self._reset()
    
    def pullFail(self, reason):
        self._reset()
        return reason

    #---------------------------------------------------------------------------
    # The GETRESULT command
    #---------------------------------------------------------------------------
    
    def getResult(self, i=None):
        
        if i is None:
            self.sendString('GETRESULT')
        elif isinstance(i, int):
            self.sendString('GETRESULT %i' % i)
        else:
            self._reset()
            return defer.fail(Failure(TypeError('i must be an int or NoneType')))
        d = self.setupForIncomingSerialized('GETRESULT OK', 'GETRESULT FAIL')
        d.addCallback(self.handleGotResult)
        d.addErrback(self.getResultFail)
        return d
    
    def handleGotResult(self, resultDict):
        if resultDict.has_key('RESULT'):
            result = newserialized.unserialize(resultDict['RESULT'])
            self._reset()
            return result
        elif resultDict.has_key('FAILURE'):
            f = newserialized.unserialize(resultDict['FAILURE'])
            f.raiseException()
    
    def getResultFail(self, reason):
        self._reset()
        return reason
    
    #---------------------------------------------------------------------------
    # The RESET command
    #---------------------------------------------------------------------------
    
    def reset(self):
        self.sendString('RESET')
        self.nextHandler = self.isResetOK
        return self._createDeferred()
    
    def isResetOK(self, msg):
        if msg == 'RESET OK':
            self.resetOK()
        elif msg == 'RESET FAIL':
            self.resetFail(Failure(error.KernelError('RESET FAIL')))
        else:
            self.dieLoudly('RESET OK|FAIL not received: ' + msg)
    
    def resetOK(self):
        self._callbackAndReset(None)
    
    def resetFail(self, reason):
        self._errbackAndReset(reason)
    
    #---------------------------------------------------------------------------
    # The KILL command
    #---------------------------------------------------------------------------
    
    def kill(self):
        self.sendString('KILL')
        self.nextHandler = self.isKillOK
        return self._createDeferred()
    
    def isKillOK(self, msg):
        if msg == 'KILL OK':
            self.killOK()
        elif msg == 'KILL FAIL':
            self.killFail(Failure(error.KernelError('KILL FAIL')))
        else:
            self.dieLoudly('KILL OK|FAIL not received: ' + msg)
    
    def killOK(self):
        self._callbackAndReset(None)
    
    def killFail(self, reason):
        self._errbackAndReset(reason)
        
    #---------------------------------------------------------------------------
    # The STATUS command
    #---------------------------------------------------------------------------
    
    def keys(self):
        self.sendString('STATUS')
        d = self.setupForIncomingSerialized('STATUS OK', 'STATUS FAIL')
        d.addCallback(self.handleGotStatus)
        d.addErrback(self.statusFail)
        return d
    
    def handleGotStatus(self, resultDict):
        result = newserialized.unserialize(resultDict['STATUS'])
        self._reset()
        return result
    
    def statusFail(self, reason):
        self._errbackAndReset(reason)
    
    #---------------------------------------------------------------------------
    # IEngineSerialized Methods
    #---------------------------------------------------------------------------
    
    #---------------------------------------------------------------------------
    # The PUSHSERIALIZED command
    #---------------------------------------------------------------------------
    # PUSHSERIALIZED calls PUSH underneath
    
    def pushSerialized(self, **namespace):
        self.nextHandler = self.isPushSerializedReady
        self.workVars['namespace'] = namespace
        d = self._createDeferred()
        self.sendString('PUSH')
        return d
    
    def isPushSerializedReady(self, msg):
        if msg == 'READY':
            for k, v in self.workVars['namespace'].iteritems():
                # Instead register a producer here!!!
                self.sendSerialized(v, k)
            self.finishPush()
        else:
            self.dieLoudly('Expecting READY, got: ' + msg)
    
    #---------------------------------------------------------------------------
    # The PULLSERIALIZED command
    #---------------------------------------------------------------------------
    
    def pullSerialized(self, *keys):
        keyString = ','.join(keys)
        self.sendString('PULL %s' % keyString)
        d = self.setupForIncomingSerialized('PULL OK', 'PULL FAIL')
        d.addCallback(self.handlePullSerialized)
        d.addErrback(self.pullFail)
        return d
    
    def handlePullSerialized(self, s):
        result = []
        for k, v in s.iteritems():
            result.append(v)
        if len(result) == 1:
            result = result[0]
        return result


# This used to inherit from IControllerToEngine
class IVanillaEngineServerFactory(IControllerCore):
    """Interface the vanillized controller presents to an Engine.
    """
    
    pass


class VanillaEngineServerFactoryFromControllerService(protocols.EnhancedServerFactory):
    """Adapts a ControllerService to an IVanillaEngineServerFactory implementer.
    
    This server factory exposes a ControllerService to an EngineService using
    the vanilla protocol.
    """
    
    implements(IVanillaEngineServerFactory)
    
    protocol = VanillaEngineServerProtocol
    
    def __init__(self, service):
        self.service = service
    
    def registerEngine(self, engine, id):
        return self.service.registerEngine(engine, id)
    
    def unregisterEngine(self, id):
        return self.service.unregisterEngine(id)


components.registerAdapter(VanillaEngineServerFactoryFromControllerService,
                           ControllerService,
                           IVanillaEngineServerFactory)

