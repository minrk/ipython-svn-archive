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
        desiredID = self.factory.getID()
        if desiredID is not None:
            self.sendString("REGISTER %i" % desiredID)
        else:
            self.sendString("REGISTER")
        self.nextHandler = self.handleRegister
    
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
            # Handler resolved with state and cmd 
            f(args)
        else:
            self.sendString('BAD COMMAND')
            self._reset()
    
    # Utility methods
        
    def defaultHandler(self, msg):
        log.msg('Unexpected message: ' + msg)
    
    def _reset(self):
        self.workVars = {}
        self.nextHandler = self.dispatch
    
    def handleUnexpectedData(self, args):
        log.msg("Unexpected Data: %s" + args)
    
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
        # args = 'REGISTER id'
        splitArgs = args.split(' ',1)
        if len(splitArgs) == 2 and splitArgs[0] == 'REGISTER':
            try:
                id = int(splitArgs[1])
            except TypeError:
                self.sendString('BAD ID')
            else:
                self.factory.setID(id)
                self._reset()
    
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
        self.sendString('EXECUTE OK')
        self._reset()
         
    def executeFail(self):
        self.sendString('EXECUTE FAIL')
        self._reset()
    
    #####   
    ##### The PUSH command
    #####
    
    def handle_PUSH(self, args):
        if args is not None:
            self.pushFail(Failure(Exception()))
        else:
            self.nextHandler = self.handlePushing
            self.workVars['pushSerialsList'] = []
            self.sendString("PUSH READY")
    
    def handlePushing(self, msg):
        if msg == 'PUSH DONE':
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
                self.pushFail(Failure(Exception()))
        else:
            self.pushFail(Failure(Exception()))
                
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
        self.factory.pushSerialized(**ns)
        self.pushOK()
            
    def pushOK(self):
        self.sendString('PUSH OK')
        self._reset()
         
    def pushFail(self, reason):
        reason.printTraceback()
        self.sendString('PUSH FAIL')
        self._reset()

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
        self.sendString('PULL OK')
        self._reset()
    
    def pullFail(self, reason):
        self.sendString('PULL FAIL')
        self._reset()

    #####
    ##### The PULLNAMESPACE command
    #####

    def handle_PULLNAMESPACE(self, args):

        keys = args.split(',')
        self.nextHandler = self.handleUnexpectedData
        d = self.factory.pullNamespaceSerialized(*keys)
        d.addCallbacks(self.handleNamespacePulled, self.pullNamespaceFail)
        return d
    
    def handleNamespacePulled(self, namespace):
        for v in namespace.itervalues():
            self.sendSerialized(v)
        self.pullNamespaceOK()
    
    def pullNamespaceOK(self):
        self.sendString('PULLNAMESPACE OK')
        self._reset()
    
    def pullNamespaceFail(self, reason):
        self.sendString('PULLNAMESPACE FAIL')
        self._reset()

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
                self.getResultFail()
            else:
                d = self.factory.getResult(index)
        d.addCallbacks(self.handleResult, self.getResultFail)
        
    def handleResult(self, result):
        serial = serialized.PickleSerialized('RESULT')
        try:
            serial.packObject(result)
        except pickle.PickleError:
            self.getResultFail()
        else:
            self.sendPickleSerialized(serial)
            self.getResultOK()
            
    def getResultOK(self):
        self.sendString('GETRESULT OK')
        self._reset()

    def getResultFail(self, reason):
        self.sendString('GETRESULT FAIL')
        self._reset()
            
    #####
    ##### The RESET command
    #####   
            
    def handle_RESET(self, args):
        d = self.factory.reset()
        d.addCallbacks(self.resetOK, self.resetFail)

    def resetOK(self, args):
        self.sendString('RESET OK')
        self._reset()

    def resetFail(self, reason):
        self.sendString('RESET FAIL')
        self._reset()

    #####
    ##### The KILL command
    #####   
            
    def handle_KILL(self, args):
        d = self.factory.kill()
        d.addCallbacks(self.killOK, self.killFail)

    def killOK(self, args):
        self.sendString('KILL OK')
        self._reset()

    def killFail(self, reason):
        self.sendString('KILL FAIL')
        self._reset()

    #####
    ##### The KILL command
    #####   
            
    def handle_KILL(self, args):
        d = self.factory.kill()
        d.addCallbacks(self.killOK, self.killFail)

    def killOK(self, args):
        self.sendString('KILL OK')
        self._reset()

    def killFail(self, reason):
        self.sendString('KILL FAIL')
        self._reset()

    #####
    ##### The STATUS command
    #####   
            
    def handle_STATUS(self, args):
        d = self.factory.status()
        d.addCallbacks(self.statusOK, self.statusFail)

    def statusOK(self, args):
        self.sendString('STATUS OK')
        self._reset()

    def statusFail(self, reason):
        self.sendString('STATUS FAIL')
        self._reset()


class IVanillaEngineClientFactory(zi.Interface):
    
    def getID():
        """Get's the engines id."""
        
    def setID(id):
        """Set's the engines id."""

class VanillaEngineClientFactoryFromEngineService(protocol.ClientFactory):
    
    zi.implements(IVanillaEngineClientFactory)
    
    protocol = VanillaEngineClientProtocol
    
    def __init__(self, service):
        self.service = service
        self.serviceInterfaces = list(zi.providedBy(service))
        
    # From IVanillaEngineClientFactory
    def getID(self):
        return self.service.id
        
    def setID(self, id):
        # Add some error checking.
        self.service.id = id
        
    # Go through the methods of service and wrap automatically!!!
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
        
    def pullNamespaceSerialized(self, *keys):
        return self.service.pullNamespaceSerialized(*keys)        
    
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
    id = None
    
    def connectionMade(self):
        self.transport.setTcpNoDelay(True)
        self.nextHandler = self.dispatch

    def connectionLost(self, reason):
        self.factory.unregisterEngine(self.id)

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
            # Handler resolved with state and cmd 
            f(args)
        else:
            #self.sendString('BAD COMMAND')
            self._reset()

    # Utility methods
        
    def defaultHandler(self, msg):
        log.msg('Unexpected message: ' + msg)
            
    def _reset(self):
        self.workVars = {}
        self.nextHandler = self.dispatch

    def _createDeferred(self):
        self.workVars['deferred'] = defer.Deferred()
        return self.workVars['deferred']

    def handleUnexpectedData(self, args):
        log.msg('Unexpected Data: %s' % args)
    
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
            self.workVars['deferred'].errback(Failure(error.ProtocolError(msg)))
            return
            
        msgList = msg.split(' ', 1)
        if len(msgList) == 2:
            serialType = msgList[0]
            self.workVars['serialKey'] = msgList[1]
            f = getattr(self, 'handleSerial_%s' % serialType, None)
            if f is not None:
                self.nextHandler = f
            else:
                self.workVars['deferred'].errback(Failure(error.ProtocolError(msg)))
        else:
            self.workVars['deferred'].errback(Failure(error.ProtocolError(msg)))
                
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
        self.sendString('REGISTER %i' % id)
        self._reset()
        
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
        if msg == 'PUSH READY':
            for k, v in self.workVars['namespace'].iteritems():
                try:
                    s = serialized.serialize(k, v)
                except pickle.PickleError:
                    self.pushFail(Failure())
                self.sendSerialized(serialized.serialize(k, v))
            self.finishPush()
        else:
            self.pushFail(Failure(Exception()))
            
    def finishPush(self):
        self.sendString('PUSH DONE')
        self.nextHandler = self.isPushOK
            
    def isPushOK(self, msg):
        if msg == 'PUSH OK':
            self.pushOK()
        else:
            self.pushFail(Failure(Exception()))
            
    def pushFail(self, f):
        self.workVars['deferred'].errback(f)
        self._reset()
        
    def pushOK(self, result=None):
        self.workVars['deferred'].callback(result)
        self._reset()
        
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
            result = listOfSerialized[0].unpack()
        else:
            result = []
            for s in listOfSerialized:
                result.append(s.unpack())
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
            result[s.key] = s.unpack()
        self.pullNamespaceOK()
        return value
            
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
            return defer.fail(Failure(Exception()))
        d = setupForIncomingSerialized('GETRESULT OK', 'GETRESULT FAIL')
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
            self.resetFail(Failure(Exception()))
        else:
            self.resetFail(Failure(Exception()))
            
    def resetOK(self):
        self.workVars['deferred'].callback(None)
        self._reset()
        
    def resetFail(self, reason):
        self.workVars['deferred'].errback(reason)
        self._reset()
        
    # KILL

    def kill(self):
        self.sendString('KILL')
        self.nextHandler = self.isKillOK
        return self._createDeferred()
        
    def isKillOK(self, msg):
        if msg == 'KILL OK':
            self.killOK()
        elif msg == 'KILL FAIL':
            self.killFail(Failure(Exception()))
        else:
            self.killFail(Failure(Exception()))
            
    def killOK(self):
        self.workVars['deferred'].callback(None)
        self._reset()
        
    def killFail(self, reason):
        self.workVars['deferred'].errback(reason)
        self._reset()
        
    # STATUS
    
    def status(self):
        self.sendString('STATUS')
        self.nextHandler = self.isStatusOK
        return self._createDeferred()
        
    def isStatusOK(self, msg):
        if msg == 'STATUS OK':
            self.statusOK()
        elif msg == 'STATUS FAIL':
            self.statusFail(Failure(Exception()))
        else:
            self.statusFail(Failure(Exception()))
            
    def statusOK(self):
        self.workVars['deferred'].callback(None)
        self._reset()
        
    def statusFail(self, reason):
        self.workVars['deferred'].errback(reason)
        self._reset()
        
    # IEngineSerialized Methods
    
    # PUSHSERIALIZED -> PUSH
    
    def pushSerialized(self, **namespace):
        self.workVars['namespace'] = namespace
        self.sendString('PUSH')
        self.nextHandler = self.isPushSerializedReady
        d = self._createDeferred()
        return d
        
    def isPushSerializedReady(self, msg):
        if msg == 'PUSH READY':
            for v in self.workVars['namespace'].itervalues():
                self.sendSerialized(v)
            self.finishPush()
        else:
            self.pushFail(Failure(Exception()))
    
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
        self.service.registerSerializationTypes(serialized.PickleSerialized,
            serialized.ArraySerialized)
    
components.registerAdapter(VanillaEngineServerFactoryFromControllerService,
                           ControllerService,
                           IVanillaEngineServerFactory)

    
