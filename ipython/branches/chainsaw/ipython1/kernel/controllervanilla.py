
"""The Twisted core of the ipython controller.

This module contains the Twisted protocols, factories, etc. used to
implement the ipython controller.  This module only contains the network related
parts of the controller.
"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import cPickle as pickle

from twisted.internet import protocol, defer
from twisted.internet.interfaces import IProducer
from twisted.python import components, log
from twisted.python.failure import Failure
from zope.interface import Interface, implements

from ipython1.kernel import controllerservice, serialized, protocols


class NonBlockingProducer:
    """A producer for nonblocking commands.  It waits for the consumer to 
    perform its next write, then makes a callback."""
    implements(IProducer)
    
    def __init__(self, protocol):
        self.factory = protocol.factory
        self._reset()
    
    def _reset(self):
        self.consumer = None
        self.deferred = None
        self.firstCall = True
    
    def register(self, consumer, deferred):
        self.consumer = consumer
        self.deferred = deferred
        consumer.registerProducer(self, False)
    
    def resumeProducing(self):
        if self.firstCall:
            self.firstCall = False
            return
        self.deferred.callback(None)
        self.consumer.unregisterProducer()
        self._reset()
        return self.deferred
    
    def pauseProducing(self):
        pass
    
    def stopProducing(self):
        log.msg("stopped producing!")
        self._reset()
    

class VanillaControllerProtocol(protocols.EnhancedNetstringReceiver):
    """The control protocol for the Controller.  It listens for clients to
    connect, and relays commands to the controller service.
    A line based protocol."""
    
    nextHandler = None
    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self.producer = NonBlockingProducer(self)
        self._reset()
    
    
    def stringReceived(self, string):
        if self.nextHandler is None:
            self.defaultHandler(string)
        else:
            self.nextHandler(string)
    
    def dispatch(self, string):
        splitString = string.split(" ", 1)
        cmd = splitString[0]
        if len(splitString) is 1:
            args = None
            targets = 'all'
        elif len(splitString) is 2:
            arglist = splitString[1].split('::')
            args = arglist[0]
            if len(arglist) > 1:
                targets = self.parseTargets(arglist[1:])
                if not self.factory.verifyTargets(targets):
                    self._reset()
                    self.sendString("BAD ID LIST")
                    return
            else:
                targets = 'all'
        f = getattr(self, 'handle_%s' %(cmd), None)
        if f:
            # Handler resolved with state and cmd 
            f(args, targets)
        else:
            self._reset()
            self.sendString("BAD COMMAND")
    
    def handleUnexpectedData(self, args):
        self.sendString('UNEXPECTED DATA')
    
    defaultHandler = handleUnexpectedData
    
    def _reset(self):
        self.workVars = {}
        self.nextHandler = self.dispatch
    
    def parseTargets(self, targetsList):
        
        if len(targetsList) is 0:
            return 'all'
        else:
            if targetsList[0] == 'all':
                return 'all'
            try:
                return map(int, targetsList)
            except:
                #defaults to all on bad targetList  should it do this
                return None
    
    #####   
    ##### The PUSH command
    #####
    
    def handle_PUSH(self, args, targets):
        self.nextHandler = self.handlePushing
        self.workVars['pushTargets'] = targets
        self.workVars['pushDict'] = {}
        self.sendString("PUSH READY")
    
    def handlePushing(self, args):
        if args == "PUSH DONE":
            return self.handlePushingDone()
        arglist = args.split(' ',1)
        if len(arglist) is 2:
            pushType = arglist[0]
            self.workVars['pushKey'] = arglist[1]
        else:
            self.pushFinish("FAIL")
            return
        
        f = getattr(self, 'handlePushing_%s' %pushType, None)
        if f is not None:
            self.nextHandler = f
        else:
            self.pushFinish("FAIL")
    
    def handlePushing_PICKLE(self, package):
        self.nextHandler = self.handlePushing
        key = self.workVars['pushKey']
        serial = serialized.PickleSerialized(key)
        serial.addToPackage(package)
        self.workVars['pushDict'][key] = serial
    
    def handlePushing_ARRAY(self, pShape):
        self.nextHandler = self.handlePushingArray_dtype
        key = self.workVars['pushKey']
        serial = serialized.ArraySerialized(key)
        serial.addToPackage(pShape)
        self.workVars['pushSerial'] = serial
    
    def handlePushingArray_dtype(self, dtype):
        self.nextHandler = self.handlePushingArray_buffer
        self.workVars['pushSerial'].addToPackage(dtype)
    
    def handlePushingArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handlePushing
        key = self.workVars['pushKey']
        self.workVars['pushSerial'].addToPackage(arrayBuffer)
        self.workVars['pushDict'][key] = self.workVars['pushSerial']
    
    def handlePushingDone(self):
        self.nextHandler = self.handleUnexpectedData
        d = defer.Deferred().addCallback(self.pushCallback)
        self.producer.register(self.transport, d)
        self.sendString('PUSH OK')
        return d
    
    def pushCallback(self, _):
        dikt = self.workVars['pushDict']
        targets = self.workVars['pushTargets']
        self._reset()
        return self.factory.pushSerialized(targets, 
                    **dikt)
    
    def pushFinish(self,msg):
        self._reset()
        self.sendString("PUSH %s" % msg)
    
    #####
    ##### The PULL command
    #####
    
    def handle_PULL(self, args, targets):
        # Parse the args
        try:
            self.workVars['pullKeys'] = args.split(',')
        except TypeError:
            self.pullFinish('FAIL')
        else:
            self.nextHandler = self.handleUnexpectedData
            d = self.factory.pullSerialized(targets, *self.workVars['pullKeys'])
            d.addCallbacks(self.pullOK, self.pullFail)
            return d
    
    def pullOK(self, entireResultList):
        for perTargetResultList in entireResultList:
            if len(self.workVars['pullKeys']) == 1:
                perTargetResultList = [perTargetResultList]
            for serialResult in perTargetResultList:
                if not isinstance(serialResult, serialized.Serialized):
                    try:
                        serialResult = serialized.serialize(serialResult, '_')
                    except:
                        self.pullFail()
                self.sendSerial(serialResult)
            
            self.sendString("SEGMENT PULLED")
        self.pullFinish("OK")
    
    def sendSerial(self, s):
        if s[0].split(' ')[0] == 'ARRAY':
            self.sendSerialArray(s)
        else:
            for line in s:
                self.sendString(line)
    
    def sendSerialArray(self, sArray):
        for line in sArray[:-1]:
            self.sendString(line)
        self.sendBuffer(sArray[-1])
    
    def pullFail(self, failure):
        self.pullFinish("FAIL")
    
    def pullFinish(self, msg):
        self._reset()
        self.sendString("PULL %s" % msg)
    
    
    #####
    ##### The SCATTER command
    #####
    
    def handle_SCATTER(self, args, targets):
        if not args:
            self.nextHandler = self.handleScatter
            return
        argSplit = args.split(' ',1)
        self.workVars['scatterTargets'] = targets
        for a in argSplit:
            split = a.split('=',1)
            if len(split) is 2:
                if split[0] == 'style':
                    self.workVars['scatterStyle'] = split[1]
                elif split[0] == 'flatten':
                    self.workVars['scatterFlatten'] = int(split[1])
                else:
                    self.scatterFail()
                    return
            else:
                self.scatterFail()
                return
        self.nextHandler = self.handleScatter
    
    def handleScatter(self, args):
        arglist = args.split(' ',1)
        if len(arglist) is 2:
            scatterType = arglist[0]
            self.workVars['scatterKey'] = arglist[1]
        else:
            self.scatterFinish("FAIL")
            return
        
        f = getattr(self, 'handleScatter_%s' %scatterType, None)
        if f is not None:
            self.nextHandler = f
        else:
            self.scatterFinish("FAIL")
    
    def handleScatter_PICKLE(self, package):
        self.nextHandler = self.handleScatterDone
        key = self.workVars['scatterKey']
        serial = serialized.PickleSerialized(key)
        serial.addToPackage(package)
        self.workVars['scatterSerial'] = serial
    
    def handleScatter_ARRAY(self, pShape):
        self.nextHandler = self.handleScatterArray_dtype
        key = self.workVars['scatterKey']
        serial = serialized.ArraySerialized(key)
        serial.addToPackage(pShape)
        self.workVars['scatterSerial'] = serial
    
    def handleScatterArray_dtype(self, dtype):
        self.nextHandler = self.handleScatterArray_buffer
        self.workVars['scatterSerial'].addToPackage(dtype)
    
    def handleScatterArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handleScatterDone
        key = self.workVars['scatterKey']
        self.workVars['scatterSerial'].addToPackage(arrayBuffer)
    
    def handleScatterDone(self, args):
        if args != "SCATTER DONE":
            return self.scatterFail()
        
        d = defer.Deferred().addCallback(self.scatterCallback)
        self.producer.register(self.transport, d)
        self.sendString('SCATTER OK')
        return d
    
    def scatterCallback(self, _):
        key = self.workVars['scatterKey']
        targets = self.workVars['scatterTargets']
        obj = self.workVars['scatterSerial'].unpack()
        kw = {}
        style = self.workVars.get('scatterStyle', None)
        if style is not None:
            kw['style'] = style
        flatten = self.workVars.get('scatterFlatten', None)
        if flatten is not None:
            kw['flatten'] = flatten
        self._reset()
        return self.factory.scatter(targets, key, obj, **kw)
    
    def scatterFail(self, failure=None):
        self.scatterFinish("FAIL")
    
    def scatterFinish(self, msg):
        self._reset()
        self.sendString("SCATTER ", msg)
    
    #####
    ##### The EXECUTE command
    #####
    
    def handle_EXECUTE(self, args, targets):
        """Handle the EXECUTE command."""
                
        # Parse the args
        if not args:
            self.executeFinish("FAIL")
            return
        
        if args[:5] == "BLOCK":
            block = True
            execute_cmd = args[6:]
        else:
            block = False
            execute_cmd = args
        
        if not execute_cmd:
            self.executeFinish("FAIL")
            return
        
        self.nextHandler = self.handleUnexpectedData

        if block:
            d = self.factory.execute(targets,execute_cmd)
            d.addCallback(self.executeBlockOK)
            d.addErrback(self.executeFail)
        else:
            self.workVars['execute_cmd'] = execute_cmd
            self.workVars['execute_targets'] = targets
            d = defer.Deferred().addCallback(self.executeCallback)
            self.producer.register(self.transport, d)
            self.sendString('EXECUTE OK')
            return d
    
    def executeCallback(self, _):
        execute_cmd = self.workVars['execute_cmd']
        targets = self.workVars['execute_targets']
        self._reset()
        return self.factory.execute(targets, execute_cmd)
    
    def executeBlockOK(self, results):
        for r in results:
            try:
                if isinstance(r, Failure):
                    serial = serialized.serialize(r, 'FAILURE')
                else:
                    serial = serialized.serialize(r, 'RESULT')
            except pickle.PickleError, e:
                self.executeFinish("FAIL")
            else:
                self.sendSerial(serial)
        self.executeFinish("OK")
    
    def executeFail(self, f):
        self.executeFinish("FAIL")
    
    def executeFinish(self, msg):
        self._reset()
        self.sendString("EXECUTE %s" % msg)
    
    #####
    ##### GETRESULT command
    #####
    
    def handle_GETRESULT(self, args, targets):
        
        self.nextHandler = self.handleUnexpectedData
        try: 
            index = int(args)
        except ValueError:
            index = None
        d = self.factory.getResult(targets, index)
        d.addCallbacks(self.getResultOK, self.getResultFail)
    
    def getResultOK(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.pickleError:
            self.getResultFinish("FAIL")
            return
        else:
            self.sendString("PICKLE RESULT")
            self.sendString(package)
            self.getResultFinish("OK")
    
    def getResultFail(self, f):
        self.getResultFinish("FAIL")
    
    def getResultFinish(self, msg):
        self._reset()
        self.sendString("GETRESULT %s" %msg)
    
    
    #####
    ##### Kernel control commands
    #####
    
    def handle_STATUS(self, args, targets):
        self.nextHandler = self.handleUnexpectedData
        d = self.factory.status(targets).addCallbacks(
            self.statusOK, self.statusFail)
        return d
    
    def statusOK(self, status):
        try:
            serial = serialized.serialize(status, 'STATUS')
        except pickle.PickleError:
            self.statusFinish('FAIL')
        else:
            self.sendSerial(serial)
            self.statusFinish('OK')
    
    def statusFail(self, reason):
        self.statusFinish("FAIL")
    
    def statusFinish(self, msg):
        self._reset()
        self.sendString("STATUS %s" % msg)
    
    def handle_NOTIFY(self, args, targets):
        self.nextHandler = self.handleUnexpectedData
        if not args:
            self.notifyFail()
            return
        else:
            args_split = args.split(" ")
            
        if len(args_split) is 3:
            action, host, port = args_split
            try:
                port = int(port)
            except ValueError:
                self.notifyFail()
            else:
                if action == "ADD":
                    return self.factory.addNotifier((host, port)
                    ).addCallbacks(self.notifyOK, self.notifyFail)
                elif action == "DEL":
                    return self.factory.delNotifier((host, port)
                    ).addCallbacks(self.notifyOK, self.notifyFail)
                else:
                    self.notifyFail()
        else:
            self.notifyFail()
    
    def notifyOK(self, s):
        self.notifyFinish("OK")
    
    def notifyFail(self, f=None):
        self.notifyFinish("FAIL")
    
    def notifyFinish(self, msg):
        self._reset()
        self.sendString("NOTIFY %s" % msg)
    # The RESET, KILL and DISCONNECT commands
    
    def handle_RESET(self, args, targets):
        self._reset()
        self.sendString('RESET OK')
        return self.factory.reset(targets)
    
    def handle_KILL(self, args, targets):
        self._reset()
        self.sendString('KILL OK')
        return self.factory.kill(targets)
    
    def handle_DISCONNECT(self, args, targets):
        log.msg("Disconnecting client...")
        self._reset()
        self.sendString("DISCONNECT OK")
        self.transport.loseConnection()
    

class IVanillaControllerFactory(Interface):
    """interface to clients for controller"""
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, targets):
        """Cleans out pending commands in an engine's queue."""
    
    #IEngine multiplexer methods
    def execute(self, targets, lines):
        """Execute lines of Python code."""
    
    def pushSerialized(self, targets, **namespace):
        """push value into locals namespace with name key."""
    
    def pullSerialized(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
    
    def pullNamespace(self, targets, *keys):
        """Gets an item out of the user namespace by key."""
    
    def status(self, targets):
        """status of engines"""
    
    def reset(self, targets):
        """Reset the InteractiveShell."""
    
    def kill(self, targets):
        """kill engines"""
    
    def getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
    


class VanillaControllerFactoryFromService(protocol.ServerFactory):
    """the controller factory"""
    
    implements(IVanillaControllerFactory)
    
    protocol = VanillaControllerProtocol
    
    def __init__(self, service):
        self.service = service
    
    def addNotifier(self, n):
        return self.service.addNotifier(n)
    
    def delNotifier(self, n):
        return self.service.delNotifier(n)
    
    def verifyTargets(self, targets):
        return self.service.verifyTargets(targets)
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, targets):
        """Cleans out pending commands in an engine's queue."""
        return self.service.cleanQueue(targets)
    
    #IEngine multiplexer methods
    def execute(self, targets, lines):
        """Execute lines of Python code."""
        d = self.service.execute(targets, lines)
        return d
        
    def pushSerialized(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        return self.service.pushSerialized(targets, **namespace)
    
    def pullSerialized(self, targets, *keys):
        """Gets an item out of the user namespace by key."""
        return self.service.pullSerialized(targets, *keys)
    
    def pullNamespaceSerialized(self, targets, *keys):
        """Gets an item out of the user namespace by key."""
        return self.service.pullNamespaceSerialized(targets, *keys)
    
    def status(self, targets):
        """status of engines"""
        return self.service.status(targets)
    
    def reset(self, targets):
        """Reset the InteractiveShell."""
        return self.service.reset(targets)
    
    def kill(self, targets):
        """kill an engine"""
        return self.service.kill(targets)
    
    def getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        return self.service.getResult(targets, i)
    


components.registerAdapter(VanillaControllerFactoryFromService,
                        controllerservice.ControllerService,
                        IVanillaControllerFactory)
