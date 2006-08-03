
"""The Twisted core of the ipython controller.

This module contains the Twisted protocols, factories, etc. used to
implement the ipython controller.  This module only contains the network related
parts of the controller.
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import cPickle as pickle
import time

from twisted.internet import protocol, defer, reactor
from twisted.internet.interfaces import IProducer
from twisted.protocols import basic
from twisted.python import components, log

from zope.interface import Interface, implements

from ipython1.kernel import controllerservice


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
    

class LiteralString:
    def __init__(self, size, defered):
        self.size = size
        self.data = []
        self.defer = defered
    
    def write(self, data):
        self.size -= len(data)
        passon = None
        if self.size > 0:
            self.data.append(data)
        else:
            if self.size:
                data, passon = data[:self.size], data[self.size:]
            else:
                passon = ''
            if data:
                self.data.append(data)
            if passon == '':
                self.defer.callback(''.join(self.data))
        return passon
    

class VanillaControllerProtocol(basic.NetstringReceiver):
    """The control protocol for the Controller.  It listens for clients to
    connect, and relays commands to the controller service.
    A line based protocol."""
    
    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self._reset()
        self.producer = NonBlockingProducer(self)
    
    
    def stringReceived(self, string):
        split_string = string.split(" ", 1)
        cmd = split_string[0]
        if len(split_string) is 1:
            args = None
            targets = 'all'
        elif len(split_string) is 2:
            if self.state == 'init':
                arglist = split_string[1].split('::')
                if len(arglist) > 1:
                    targets = self.parseTargets(arglist[1:])
                    if not self.factory.verifyTargets(targets):
                        self.sendString("BAD ID LIST")
                        self._reset()
                        return
                else:
                    targets = 'all'
                args = arglist[0]
            else:
                args = split_string[1]
                targets = None
        
        
        f = getattr(self, 'handle_%s_%s' %
                    (self.state, cmd), None)            
        if f:
            # Handler resolved with state and cmd 
            f(args, targets)
        else:
            f = getattr(self, 'handle_%s' %
                (cmd), None)
            if f:
                # Handler resolved with only cmd
                f(args, targets)
            else:
                self.sendString("BAD COMMAND")
                self._reset()
    
    def _reset(self):
        self.workVars = {}
        self.state = 'init'
    
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
    
    def handle_init_PUSH(self, args, targets):
        
        # Parse the args
        self.workVars['push_targets'] = targets
        # Setup to process the command
        self.state = 'pushing'
    
    def handle_pushing_PICKLE(self, pickledNamespace, _):
        self.workVars['push_pickledNamespace'] = pickledNamespace
        d = defer.Deferred().addCallback(self.pushCallback)
        self.producer.register(self.transport, d)
        self.sendString("PUSH OK")
        return d
    
    def pushCallback(self, _):
        pickledNamespace = self.workVars['push_pickledNamespace']
        targets = self.workVars['push_targets']
        self._reset()
        return self.factory.pushPickle(targets, pickledNamespace)
    
    def pushFinish(self,msg):
        self.sendString("PUSH %s" % msg)
        self._reset()
    
    #####
    ##### The PULL command
    #####

    def handle_init_PULL(self, args, targets):
        # Parse the args
        try:
            keys = tuple(args.split(','))
        except TypeError:
            self.pushFinish('FAIL')
        else:
            d = self.factory.pullPickle(targets, *keys)
            d.addCallbacks(self.pullOK, self.pullFail)
            return d
    
    def pullOK(self, pResultList):
        try:
            #get list of pickles, want pickled list
            #this is slow and not good
            resultList = map(pickle.loads, pResultList)
            presult = pickle.dumps(resultList, 2)
        except pickle.PickleError, TypeError:
            self.pullFinish("FAIL")
        else:
            self.sendString("PICKLE %s" % presult)
            self.pullFinish("OK")
    
    def pullFail(self, failure):
        self.pullFinish("FAIL")
    
    def pullFinish(self, msg):
        self.sendString("PULL %s" % msg)
        self._reset()
    
    #####
    ##### The EXECUTE command
    #####
    
    def handle_init_EXECUTE(self, args, targets):
        """Handle the EXECUTE command."""
                
        # Parse the args
        if not args:
            self.executeFinish("FAIL")
            return
        
        if "BLOCK" in args:
            block = True
            execute_cmd = args[6:]
        else:
            block = False
            execute_cmd = args
        
        if not execute_cmd:
            self.executeFinish("FAIL")
            return
        
        self.state = 'executing'
        if block:
            d = self.factory.execute(targets,execute_cmd)
            d.addCallback(self.executeOkBlock)
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
    
    def executeOkBlock(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.executeFinish("FAIL")
        else:
            self.sendString("PICKLE %s" % package)
            self.executeFinish("OK")
    
    def executeFail(self, f):
        self.executeFinish("FAIL")
    
    def executeFinish(self, msg):
        self.sendString("EXECUTE %s" % msg)
        self._reset()
    
    #####
    ##### GETRESULT command
    #####
    
    def handle_init_GETRESULT(self, args, targets):
        
        try: 
            index = int(args)
        except:
            index = None
        d = self.factory.getResult(targets, index)
        d.addCallbacks(self.getResultOK, self.getResultFail)
    
    def getResultOK(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.getResultFinish("FAIL")
        else:
            self.sendString("PICKLE %s" % package)
            self.getResultFinish("OK")
    
    def getResultFail(self, f):
        self.getResultFinish("FAIL")
    
    def getResultFinish(self, msg):
        self.sendString("GETRESULT %s" %msg)
    
    
    #####
    ##### Kernel control commands
    #####
    
    def handle_init_STATUS(self, args, targets):
        
        d = self.factory.status(targets).addCallbacks(
            self.statusOk, self.statusFail)
        return d
    
    def statusOk(self, status):
        try:
            package = pickle.dumps(status, 2)
        except pickle.PickleError:
            self.statusFinish('FAIL')
        else:
            self.sendString("PICKLE %s" % package)
            self.statusFinish('OK')
    
    def statusFail(self, reason):
        self.statusFinish("FAIL")
    
    def statusFinish(self, msg):
        self._reset()
        self.sendString("STATUS " + msg)
    
    def handle_init_NOTIFY(self, args, targets):
        if not args:
            self.notifyFail()
            return
        else:
            args_split = args.split(" ")
        
        if len(args_split) is 3:
            action, host, port = args_split
            try:
                port = int(port)
            except (ValueError, TypeError):
                self.notifyFail()
            else:
                if action == "ADD":
                    return self.factory.addNotifier((host, port)
                    ).addCallback(self.notifyFinish)
                elif action == "DEL":
                    return self.factory.delNotifier((host, port)
                    ).addCallback(self.notifyFinish)
                else:
                    self.notifyFail()
        else:
            self.notifyFail()
    
    def notifyFail(self, f=None):
        self.notifyFinish("FAIL")
    
    def notifyFinish(self, msg):
        self._reset()
        if msg is None:
            msg = "OK"
        self.sendString("NOTIFY %s" % msg)
    # The RESET, KILL and DISCONNECT commands
    
    def handle_RESET(self, args, targets):
        self.sendString('RESET OK')
        self._reset()
        return self.factory.reset(targets)
    
    def handle_KILL(self, args, targets):
        self.sendString('KILL OK')
        self._reset()
        return self.factory.kill(targets)
    
    def handle_DISCONNECT(self, args, targets):
        log.msg("Disconnecting client...")
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
    
    def push(self, targets, **namespace):
        """push value into locals namespace with name key."""
    
    def pushPickle(self, targets, pickledNamespace):
        """Unpickle package and push into the locals namespace with name key."""
    
    def pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
    
    def pullPickle(self, targets, *keys):
        """Gets an item out of the self.locals dist by key and pickles it."""
    
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
        return self.service.execute(targets, lines)
    
    def push(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        return self.service.push(targets, **namespace)
    
    def pushPickle(self, targets, pickledNamespace):
        """Push value into locals namespace with name key."""
        return self.service.pushPickle(targets, pickledNamespace)
    
    def pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.service.pull(targets, *keys)
    
    def pullPickle(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.service.pullPickle(targets, *keys)
    
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
