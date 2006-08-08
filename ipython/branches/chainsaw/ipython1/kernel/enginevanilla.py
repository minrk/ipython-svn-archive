import cPickle as pickle

import zope.interface as zi
from twisted.python import components
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic

from ipython1.kernel.controllerservice import ControllerService
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
            args = splitLine[1:]
        
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
        self.sendString('UNEXPECTED DATA')
    
    def sendPickleSerialized(self, p):
        for line in p:
            self.sendString(line)
            
    def sendArrarySerialized(self, a):
        ia = iter(a)
        self.sendString(ia.next())
        self.sendString(ia.next())
        self.sendBuffer(ia.next())

        
    def sendSerialized(self, s):
        if isinstance(s, PickleSerialized):
            self.sendPickle(s)
        elif isinstance(s, ArraySerialized):
            self.sendArray(s)
    
    #####
    ##### The REGISTER command
    #####
    
    def handleRegister(self, args):
        # args = 'REGISTER id'
        try:
            id = int(args)
        except TypeError:
            self.sendString('BAD ID')
        else:
            self.factory.setID(id)
            self._reset()
            
    #####
    ##### The EXECUTE command
    #####
            
    def handle_EXECUTE(self, lines):
        d = self.factory.execute(lines)
        d.addCallback(self.handleExecuteResult)
        d.addErrback(self.executeFail)
        self.nextHandler = self.handleUnexpectedData
        
    def handleExecuteResult(self, result):
        serial = serialized.PickleSerialized('result')
        try:
            serial.packObject(result)
        except pickle.PickleError:
            self.executeFail()
        else:
            self.sendPickleSerialized(serial)
            d.addCallback(self.executeOK)
 
    def executeOK(self, args):
        self.sendString('EXECUTE OK')
        self._reset()
         
    def executeFail(self, reason):
        self.sendString('EXECUTE FAIL')
        self._reset()
    
    #####   
    ##### The PUSH command
    #####
    
    def handle_PUSH(self, args):
        if args is not None:
            self.sendString('BAD COMMAND')
            self._reset()
        else:
            self.nextHandler = handlePushing
            self.workVars['pushSerialsList'] = []
            self.sendString("PUSH READY")
    
    def handlePushing(self, msg):
        if msg == 'PUSH DONE':
            return self.handlePushDone()
            
        msgList = msg.split(' ', 1)
        if len(msgList) == 2:
            pushType = msgList[0]
            self.workVars['pushKey'] = msgList[1]
            f = getattr(self, 'handlePushing_%s' % pushType, None)
            if f is not None:
                self.nextHandler = f
            else:
                self.pushFail()
        else:
            self.pushFail()
                
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
        self.factory.pushSerialized(**self.workVars['pushSerialsList'])
        self.pushOK()
            
    def pushOK(self, args):
        self.sendString('PUSH OK')
        self._reset()
         
    def pushFail(self, reason):
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
    
    def pullOK(self, args):
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
    
    def pullNamespaceOK(self, args):
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
        serial = serialized.PickleSerialized('result')
        try:
            serial.packObject(result)
        except pickle.PickleError:
            self.getResultFail()
        else:
            self.sendPickleSerialized(serial)
            self.getResultOK()
            
    def getResultOK(self, args):
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

class IVanillaEngineServerProtocol(zi.Interface):
    pass
    
class VanillaEngineServerProtocol(EnhancedNetstringReceiver):
    
    zi.implements(IVanillaEngineServerProtocol)

class IVanillaEngineServerFactory(zi.Interface):
    """This is what the client factory should look like"""

class VanillaEngineServerFactoryFromControllerService(protocol.ServerFactory):
    
    zi.implements(IVanillaEngineServerFactory)
    
    protocol = VanillaEngineServerProtocol
    
components.registerAdapter(VanillaEngineServerFactoryFromControllerService,
                           ControllerService,
                           IVanillaEngineServerFactory)
    
class EngineFromVanillaEngineServerProtocol(object):

    zi.implements(engineservice.IEngineBase)
    
    
components.registerAdapter(EngineFromVanillaEngineServerProtocol,
                           VanillaEngineServerProtocol,
                           engineservice.IEngineBase)

    
