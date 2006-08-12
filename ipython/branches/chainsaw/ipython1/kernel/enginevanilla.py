# -*- test-case-name: ipython1.test.test_enginevanilla -*-

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import cPickle as pickle

import zope.interface as zi
from twisted.python import components, log
from twisted.python.failure import Failure
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic

defer.setDebugging(1)

from ipython1.kernel import error
from ipython1.kernel.controllerservice import ControllerService, IRemoteController
from ipython1.kernel.protocols import EnhancedNetstringReceiver
import ipython1.kernel.serialized as serialized
import ipython1.kernel.engineservice as engineservice

# Engine side of things

class IVanillaEngineClientProtocol(zi.Interface):
    pass
    
class VanillaEngineClientProtocol(EnhancedNetstringReceiver):
    
    zi.implements(IVanillaEngineClientProtocol)

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
    
    # Utility methods
        
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
    
    def sendPickleSerialized(self, p):
        for line in p:
            self.sendString(line)
    
    def sendArrarySerialized(self, a):
        ia = iter(a)
        self.sendString(ia.next())
        self.sendString(ia.next())
        self.sendBuffer(ia.next())
    
    def sendSerialized(self, s):
        if isinstance(s, serialized.PickleSerialized):
            self.sendPickleSerialized(s)
        elif isinstance(s, serialized.ArraySerialized):
            self.sendArrarySerialized(s)
    
    #####
    ##### The REGISTER command
    #####
    
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
    
    #####
    ##### The EXECUTE command
    #####
            
    def handle_EXECUTE(self, lines):
        # This will block so callbacks are called immediately!
        if lines is None:
            self.executeFail()
        d = self.factory.execute(lines)
        d.addCallback(self.handleExecuteSuccess)
        d.addErrback(self.handleExecuteFailure)
        
    def handleExecuteSuccess(self, result):
        try:
            serial = serialized.PickleSerialized('RESULT')
            serial.packObject(result)
        except pickle.PickleError:
            self.handleExecuteFailure(Failure())
        else:
            self.sendPickleSerialized(serial)
            self.executeOK()
 
    def handleExecuteFailure(self, reason):
        # I am not sure we need to catch this PickleError
        try:
            serial = serialized.PickleSerialized('FAILURE')
            serial.packObject(reason)
        except pickle.PickleError:
            self.executeFail()
        else:
            self.sendPickleSerialized(serial)
            self.executeOK()    
 
    def executeOK(self):
        self._reset()
        self.sendString('EXECUTE OK')
    
    def executeFail(self):
        self._reset()
        self.sendString('EXECUTE FAIL')
    
    #####   
    ##### The PUSH command
    #####
    
    def handle_PUSH(self, args):
        if args is not None:
            self.dieLoudly('PUSH does not take any arguments: ' + args)
        else:
            self.nextHandler = self.handlePushing
            self.workVars['pushSerialsList'] = []
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
        serial = serialized.PickleSerialized(self.workVars['pushKey'])
        serial.addToPackage(package)
        self.workVars['pushSerialsList'].append(serial)
                
    def handlePushing_ARRAY(self, pShape):
        self.nextHandler = self.handlePushingArray_dtype
        serial = serialized.ArraySerialized(self.workVars['pushKey'])
        serial.addToPackage(pShape)
        self.workVars['pushSerial'] = serial
    
    def handlePushingArray_dtype(self, dtype):
        self.nextHandler = self.handlePushingArray_buffer
        self.workVars['pushSerial'].addToPackage(dtype)
    
    def handlePushingArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handlePushing
        self.workVars['pushSerial'].addToPackage(arrayBuffer)
        self.workVars['pushSerialsList'].append(self.workVars['pushSerial'])
                
    def handlePushDone(self):
        ns = {}
        for v in self.workVars['pushSerialsList']:
            ns[v.key] = v
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
    
    #####
    ##### The PULL command
    #####

    def handle_PULL(self, args):

        keys = args.split(',')
        self.nextHandler = self.handleUnexpectedData
        d = self.factory.pullSerialized(*keys)
        d.addCallbacks(self.handlePullingDone, self.pullFail)
        return d
    
    def handlePullingDone(self, oneOrMoreSerialized):
        if isinstance(oneOrMoreSerialized, (list, tuple)):
            for s in oneOrMoreSerialized:
                self.sendSerialized(s)
        else:
            self.sendSerialized(oneOrMoreSerialized)
        self.pullOK()
    
    def pullOK(self):
        self._reset()
        self.sendString('PULL OK')
    
    def pullFail(self, reason):
        self._reset()
        self.sendString('PULL FAIL')

    #####
    ##### The PULLNAMESPACE command
    #####

    def handle_PULLNAMESPACE(self, args):

        keys = args.split(',')
        self.nextHandler = self.handleUnexpectedData
        d = self.factory.pullNamespace(*keys)
        d.addCallbacks(self.handleNamespacePulled, self.pullNamespaceFail)
        return d
    
    def handleNamespacePulled(self, namespace):
        serialNS = {}
        try:
            for k,v in namespace.iteritems():
                serialNS[k] = serialized.serialize(v, k)
        except Exception, e:
            self.dieLoudly("serialization error: ", e)
        for v in serialNS.itervalues():
            self.sendSerialized(v)
        self.pullNamespaceOK()
    
    def pullNamespaceOK(self):
        self._reset()
        self.sendString('PULLNAMESPACE OK')
    
    def pullNamespaceFail(self, reason):
        self._reset()
        self.sendString('PULLNAMESPACE FAIL')

    #####
    ##### The GETRESULT command
    #####

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
            serial = serialized.PickleSerialized('RESULT')
            serial.packObject(result)
        except pickle.PickleError:
            self.handleGetResultFailure(Failure())
        else:
            self.sendPickleSerialized(serial)
            self.getResultOK()
 
    def handleGetResultFailure(self, reason):
        # I am not sure we need to catch this PickleError
        try:
            serial = serialized.PickleSerialized('FAILURE')
            serial.packObject(reason)
        except pickle.PickleError:
            self.getResultFail()
        else:
            self.sendPickleSerialized(serial)
            self.getResultOK()    
 
    def getResultOK(self):
        self._reset()
        self.sendString('EXECUTE OK')
    
    def getResultFail(self):
        self._reset()
        self.sendString('EXECUTE FAIL')
            
    #####
    ##### The RESET command
    #####   
            
    def handle_RESET(self, args):
        d = self.factory.reset()
        d.addCallbacks(self.resetOK, self.resetFail)

    def resetOK(self, args):
        self._reset()
        self.sendString('RESET OK')
    
    def resetFail(self, reason):
        self._reset()
        self.sendString('RESET FAIL')
    
    #####
    ##### The KILL command
    #####   
            
    def handle_KILL(self, args):
        d = self.factory.kill()
        d.addCallbacks(self.killOK, self.killFail)

    def killOK(self, args):
        self._reset()
        self.sendString('KILL OK')

    def killFail(self, reason):
        self._reset()
        self.sendString('KILL FAIL')

    #####
    ##### The STATUS command
    #####   
            
    def handle_STATUS(self, args):
        d = self.factory.status()
        d.addCallbacks(self.statusOK, self.statusFail)

    def statusOK(self, args):
        self._reset()
        self.sendString('STATUS OK')

    def statusFail(self, reason):
        self._reset()
        self.sendString('STATUS FAIL')

class IVanillaEngineClientFactory(engineservice.IEngineBase,
    engineservice.IEngineSerialized):
    
    pass

class VanillaEngineClientFactoryFromEngineService(protocol.ClientFactory):
    
    zi.implements(IVanillaEngineClientFactory)
    
    protocol = VanillaEngineClientProtocol
    
    def __init__(self, service):
        self.service = service
        
    # From IVanillaEngineClientFactory
    def _getID(self):
        return self.service.id
        
    def _setID(self, id):
        # Add some error checking.
        self.service.id = id
        self.notifySetID()   # Use as a hook for tests
        
    def notifySetID(self):
        # This is meant to be a hook to detect whenn the Protocol calls setID
        # after it has finished registering with a controller.  Mainly for tests.
        pass
        
    id = property(_getID, _setID, "The engine's id.")
    
    # These should be generated dynamically from service
    def execute(self, lines):
        return self.service.execute(lines)
        
    def push(self, **namespace):
        return self.service.push(**namespace)

    def pull(self, *keys):
        return self.service.pull(*keys)
        
    def pullNamespace(self, *keys):
        return self.service.pullNamespace(*keys)

    def getResult(self, i=None):
        return self.service.getResult(i)

    def reset(self):
        return self.service.reset()

    def kill(self):
        return self.service.kill()

    def status(self):
        return self.service.status()
        
    def pushSerialized(self, **namespace):
        return self.service.pushSerialized(**namespace)

    def pullSerialized(self, *keys):
        return self.service.pullSerialized(*keys)
             
components.registerAdapter(VanillaEngineClientFactoryFromEngineService,
                           engineservice.EngineService,
                           IVanillaEngineClientFactory)

    
# Controller side of things

class IVanillaEngineServerProtocol(engineservice.IEngineBase,
    engineservice.IEngineSerialized):
    
    pass
    
class VanillaEngineServerProtocol(EnhancedNetstringReceiver):
    
    zi.implements(IVanillaEngineServerProtocol)
    
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

    id = property(_getID, _setID, "The engine's id.")
    
    #def sendString(self, s):
    #    log.msg('C: %s' % s)
    #    EnhancedNetstringReceiver.sendString(self, s)
    
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

    # Utility methods
        
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
    
    def sendPickleSerialized(self, p):
        for line in p:
            self.sendString(line)
            
    def sendArrarySerialized(self, a):
        ia = iter(a)
        self.sendString(ia.next())
        self.sendString(ia.next())
        self.sendBuffer(ia.next())

    def sendSerialized(self, s):
        if isinstance(s, serialized.PickleSerialized):
            self.sendPickleSerialized(s)
        elif isinstance(s, serialized.ArraySerialized):
            self.sendArrarySerialized(s)

    def setupForIncomingSerialized(self, callbackString, errbackString=''):
        self.workVars['callbackString'] = callbackString
        if errbackString:
            self.workVars['errbackString'] = errbackString
        self.workVars['serialsList'] = []
        self.nextHandler = self.handleIncomingSerialized
        self.workVars['deferred'] = defer.Deferred()
        return self.workVars['deferred']
        
    def handleIncomingSerialized(self, msg):
        if msg == self.workVars['callbackString']:
            self.workVars['deferred'].callback(self.workVars['serialsList'])
            return
        elif msg == self.workVars['errbackString']:
            self.workVars['deferred'].errback(Failure(error.KernelError(msg)))
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
        serial = serialized.PickleSerialized(self.workVars['serialKey'])
        serial.addToPackage(package)
        self.workVars['serialsList'].append(serial)
                
    def handleSerial_ARRAY(self, pShape):
        self.nextHandler = self.handleArray_dtype
        serial = serialized.ArraySerialized(self.workVars['serialKey'])
        serial.addToPackage(pShape)
        self.workVars['serial'] = serial
    
    def handleArray_dtype(self, dtype):
        self.nextHandler = self.handleArray_buffer
        self.workVars['serial'].addToPackage(dtype)
    
    def handleArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handleIncomingSerialized
        self.workVars['serial'].addToPackage(arrayBuffer)
        self.workVars['serialsList'].append(self.workVars['serial'])
        
    # REGISTER

    def handle_REGISTER(self, args):
        self.nextHandler = self.handleUnexpectedData
        desiredID = args
        if desiredID is not None:
            try:
                desiredID = int(desiredID)
            except TypeError:
                desiredID = None
        qe = engineservice.QueuedEngine(self)
        self.id = self.factory.registerEngine(engineservice.completeEngine(qe), 
            desiredID)
        self.handleID(self.id)
        
    def handleID(self, id):
        self._reset()
        self.sendString('REGISTER %i' % id)

        
    # IEngineBase Methods
    
    # EXECUTE
    
    def execute(self, lines):
        if not isinstance(lines, str):
            return defer.fail(Failure(TypeError('lines must be a string')))
        self.sendString('EXECUTE %s' % lines)
        d = self.setupForIncomingSerialized('EXECUTE OK', 'EXECUTE FAIL')
        d.addCallbacks(self.handleExecuteOK, self.handleExecuteFail)
        return d
        
    def handleExecuteOK(self, listOfSerialized):
        value = listOfSerialized[0].unpack()
        self._reset()
        return value
        
    def handleExecuteFail(self, reason):
        self._reset()
        return reason
        
    # PUSH
    
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
                    s = serialized.serialize(v, k)
                except Exception, e:
                    log.msg('You tried to push an unserializable type, ignoring: ' + k) 
                else:
                    self.sendSerialized(s)
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
    
    #PULL
    
    def pull(self, *keys):
        keyString = ','.join(keys)
        self.sendString('PULL %s' % keyString)
        d = self.setupForIncomingSerialized('PULL OK', 'PULL FAIL')
        d.addCallback(self.handlePulledSerialized)
        d.addErrback(self.pullFail)
        return d
        
    def handlePulledSerialized(self, listOfSerialized):
        if len(listOfSerialized) == 1:
            try:
                result = listOfSerialized[0].unpack()
            except Exception:
                result = None
        else:
            result = []
            for s in listOfSerialized:
                try:
                    obj = s.unpack()
                except Exception:
                    log.msg('You pulled an unserializable type, ignoring: ' + s.key)
                else:
                    result.append(obj)
        self.pullOK()
        return result
            
    def pullOK(self):
        self._reset()
            
    def pullFail(self, reason):
        self._reset()
        return reason
            
    # PULLNAMESPACE
    
    def pullNamespace(self, *keys):
        keyString = ','.join(keys)
        self.sendString('PULLNAMESPACE %s' % keyString)
        d = self.setupForIncomingSerialized('PULLNAMESPACE OK', 'PULLNAMESPACE FAIL')
        d.addCallback(self.handlePulledNamespaceSerialized)
        d.addErrback(self.pullNamespaceFail)
        return d
        
    def handlePulledNamespaceSerialized(self, listOfSerialized):
        result = {}
        for s in listOfSerialized:
            try:
                obj = s.unpack()
            except Exception:
                log.msg('You pulled an unserializable type, ignoring: ' + s.key)
            else:
                result[s.key] = obj
        self.pullNamespaceOK()
        return result
            
    def pullNamespaceOK(self):
        self._reset
            
    def pullNamespaceFail(self, reason):
        self._reset()
        return reason
    
    # GETRESULT
    
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
    
    def handleGotResult(self, resultList):
        result = resultList[0].unpack()
        self._reset()
        return result
        
    def getResultFail(self, reason):
        self._reset()
        return reason
    
    # RESET
    
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
    
    # KILL

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
        
    # STATUS
    
    def status(self):
        self.sendString('STATUS')
        self.nextHandler = self.isStatusOK
        return self._createDeferred()
        
    def isStatusOK(self, msg):
        if msg == 'STATUS OK':
            self.statusOK()
        elif msg == 'STATUS FAIL':
            self.statusFail(Failure(error.KernelError('STATUS FAIL')))
        else:
            self.dieLoudly('STATUS OK|FAIL not received: ' + msg)
            
    def statusOK(self):
        self._callbackAndReset(None)
    
    def statusFail(self, reason):
        self._errbackAndReset(reason)
        
    # IEngineSerialized Methods
    
    # PUSHSERIALIZED -> PUSH
    
    def pushSerialized(self, **namespace):
        self.nextHandler = self.isPushSerializedReady
        self.workVars['namespace'] = namespace
        d = self._createDeferred()
        self.sendString('PUSH')
        return d
        
    def isPushSerializedReady(self, msg):
        if msg == 'READY':
            for v in self.workVars['namespace'].itervalues():
                self.sendSerialized(v)
            self.finishPush()
        else:
            self.dieLoudly('Expecting READY, got: ' + msg)
    
    # PULLSERIALIZED
    
    def pullSerialized(self, *keys):
        keyString = ','.join(keys)
        self.sendString('PULL %s' % keyString)
        d = self.setupForIncomingSerialized('PULL OK', 'PULL FAIL')
        d.addCallback(self.handlePullSerialized)
        d.addErrback(self.pullFail)
        return d
        
    def handlePullSerialized(self, s):
        if len(s) == 1:
            return s[0]
        else:
            return s
        
    # IEngineThreadedMethods
    
class IVanillaEngineServerFactory(IRemoteController):
    """This is what the client factory should look like"""
    
    pass

class VanillaEngineServerFactoryFromControllerService(protocol.ServerFactory):
    
    zi.implements(IVanillaEngineServerFactory)
    
    protocol = VanillaEngineServerProtocol
    
    def __init__(self, service):
        self.service = service
    
    def registerEngine(self, engine, id):
        return self.service.registerEngine(engine, id)
    
    def unregisterEngine(self, id):
        return self.service.unregisterEngine(id)
    
    def registerSerializationTypes(self, *serialTypes):
        return self.service.registerSerializationTypes(*serialTypes)
                
    def startFactory(self):
        return self.service.registerSerializationTypes(serialized.PickleSerialized,
            serialized.ArraySerialized)
    
components.registerAdapter(VanillaEngineServerFactoryFromControllerService,
                           ControllerService,
                           IVanillaEngineServerFactory)

    
