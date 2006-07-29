
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
    

class ControlTCPProtocol(basic.LineReceiver):
    
#    implements(IProducer)
    
    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self.state = 'init'
        self.workVars = {}
        self.producer = NonBlockingProducer(self)
    
    
    def lineReceived(self, line):
        split_line = line.split(" ", 1)
        if len(split_line) is 1:
            cmd = split_line[0]
            args = None
            ids = 'all'
        elif len(split_line) is 2:
            cmd = split_line[0]
            arglist = split_line[1].split('::')
            if len(arglist) > 1:
                ids = self.parseIds(arglist[1:])
            else:
                ids = 'all'
            args = arglist[0]
        
        if not self.factory.verifyIds(ids):
            self.sendLine("BAD")
            self.state = 'init'
            self.resetWorkVars()
            return
        f = getattr(self, 'handle_%s_%s' %
                    (self.state, cmd), None)            
        if f:
            # Handler resolved with state and cmd 
            f(args, ids)
        else:
            f = getattr(self, 'handle_%s' %
                (cmd), None)
            if f:
                # Handler resolved with only cmd
                f(args, ids)
            else:
                self.sendLine("BAD")
                self.state = 'init'
                self.resetWorkVars()
    
    # Copied from twisted.mail.imap4
    def rawDataReceived(self, data):
        passon = self._pendingLiteral.write(data)
        if passon is not None:
            self.setLineMode(passon) # should I reset the state here?
    
    def resetWorkVars(self):
        self.workVars = {}
    
    def _reset(self):
        self.workVars = {}
        self.state = 'init'
    
    def parseIds(self, idsList):
        if len(idsList) is 0:
            return 'all'
        else:
            try:
                return map(int, idsList)
            except:
                return 'all'
    
    #####   
    ##### The PUSH command
    #####
    
    def handle_init_PUSH(self, args, ids):
        
        # Parse the args
        if not args:
            self.pushFinish("FAIL")
            return
        else:
            args_str = args

        self.workVars['push_name'] = args_str
        self.workVars['push_ids'] = ids
        # Setup to process the command
        self.state = 'pushing'
    
    def setupLiteral(self, size):
        """Called by data command handlers."""
        d = defer.Deferred()
        self._pendingLiteral = LiteralString(size, d)
        self.setRawMode()
        return d        
    
    def pushFinish(self,msg):
        self.sendLine("PUSH %s" % msg)
        self._reset()
    
    def handle_pushing_PICKLE(self, size_str, ids):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.pushFinish("FAIL")
        else:         
            d = self.setupLiteral(size)
            d.addCallback(self.pushPickle)
    
    def pushPickle(self, package):
        try:
            data = pickle.loads(package)
            self.workVars['push_package'] = package
        except pickle.PickleError:
            self.pushFinish("FAIL")
        else:
            # What if this fails?  When could it?
            d = defer.Deferred().addCallback(self.pushCallback)
            self.producer.register(self.transport, d)
            self.sendLine("PUSH OK")
        return d
    
    def pushCallback(self, _):
        name = self.workVars['push_name']
        package = self.workVars['push_package']
        ids = self.workVars['push_ids']
        self._reset()
        return self.factory.pushPickle(name, package, ids)
    
    #####   
    ##### The UPDATE command
    #####
    
    def handle_init_UPDATE(self, args, ids):
        
        self.workVars['update_ids'] = ids
        # Setup to process the command
        self.state = 'updating'
    
    def updateFinish(self,msg):
        self.sendLine("UPDATE %s" % msg)
        self._reset()
    
    def handle_updating_PICKLE(self, size_str, ids):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.updateFinish("FAIL")
        else:         
            d = self.setupLiteral(size)
            d.addCallback(self.updatePickle)
    
    def updatePickle(self, package):
        try:
            data = pickle.loads(package)
            self.workVars['update_package'] = package
        except pickle.PickleError:
            self.updateFinish("FAIL")
        else:
            # What if this fails?  When could it?
            d = defer.Deferred().addCallback(self.updateCallback)
            self.producer.register(self.transport, d)
            self.sendLine("UPDATE OK")
            return d
    
    def updateCallback(self, _):
        package = self.workVars['update_package']
        ids = self.workVars['update_ids']
        self._reset()
        return self.factory.updatePickle(package, ids)
    
    #####
    ##### The PULL command
    #####
    
    def handle_init_PULL(self, args, ids):
        # Parse the args
        if not args:
            self.pullFinish("FAIL")
            return
        else:
            pull_name = args
            
        self.workVars['pull_type'] = 'PICKLE'
        d = self.factory.pullPickle(pull_name, ids)
                
        d.addCallback(self.pullOk)
#        d.addErrback(self.pullFail)
    
    def pullOk(self, resultList):
        try:
            result = map(pickle.loads, 
                    map(tuple.__getitem__, resultList, [1]*len(resultList)))
            presult = pickle.dumps(result, 2)
        except pickle.PickleError, TypeError:
            self.pullFinish("FAIL")
        else:
            self.sendLine("PICKLE %s" % len(presult))
            self.transport.write(presult)
            self.pullFinish("OK")
    
    def pullFail(self, failure):
        self.pullFinish("FAIL")
    
    def pullFinish(self, msg):
        self.sendLine("PULL %s" % msg)
        self._reset()
    
    #####
    ##### The EXECUTE command
    #####
    
    def handle_init_EXECUTE(self, args, ids):
        """Handle the EXECUTE command."""
                
        # Parse the args
        if not args:
            self.executeFinish("FAIL")
            return
        
        self.state = 'executing'
        if "BLOCK" in args:
            block = True
            execute_cmd = args[6:]
        else:
            block = False
            execute_cmd = args
        
        if not execute_cmd:
            self.executeFinish("FAIL")
            return
        
        if block:
            d = self.factory.execute(execute_cmd, ids)
            d.addCallback(self.executeOkBlock)
            d.addErrback(self.executeFail)
        else:
            self.workVars['execute_cmd'] = execute_cmd
            self.workVars['execute_ids'] = ids
            d = defer.Deferred().addCallback(self.executeCallback)
            self.producer.register(self.transport, d)
            self.sendLine('EXECUTE OK')
            return d
    
    def executeCallback(self, _):
        execute_cmd = self.workVars['execute_cmd']
        ids = self.workVars['execute_ids']
        self._reset()
        return self.factory.execute(execute_cmd, ids)
    
    def executeOkBlock(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.executeFinish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.executeFinish("OK")
    
    def executeFail(self, f):
        self.executeFinish("FAIL")
    
    def executeFinish(self, msg):
        self.sendLine("EXECUTE %s" % msg)
        self._reset()
    
    #####
    ##### GETCOMMAND command
    #####
    
    def handle_init_GETCOMMAND(self, args, ids):
        
        try: 
            index = int(args)
        except:
            index = None
        d = self.factory.getCommand(index, ids)
        d.addCallbacks(self.getCommandOk, self.getCommandFail)
    
    def getCommandOk(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.getCommandFinish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.getCommandFinish("OK")
    
    def getCommandFail(self, f):
        self.getCommandFinish("FAIL")
    
    def getCommandFinish(self, msg):
        self.sendLine("GETCOMMAND %s" %msg)
    
    
    #####
    ##### GETLASTCOMMANDINDEX command
    #####
    
    def handle_init_GETLASTCOMMANDINDEX(self, args, ids):
        
        d = self.factory.getLastCommandIndex(ids)
        d.addCallbacks(self.getLastCommandIndexOk, self.getLastCommandIndexFail)
    
    def getLastCommandIndexOk(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.getLastCommandIndexFinish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.getLastCommandIndexFinish("OK")
    
    def getLastCommandIndexFail(self, f):
        self.getLastCommandIndexFinish("FAIL")
    
    def getLastCommandIndexFinish(self, msg):
        self.sendLine("GETLASTCOMMANDINDEX %s" %msg)
    
    #####
    ##### Kernel control commands
    #####
    
    def handle_init_STATUS(self, args, ids):
        
        result = self.factory.status(ids)
                
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.sendLine('STATUS FAIL')
        else:
            self.sendLine("PICKLE %s" % len(package))
            self.transport.write(package)
            self.sendLine('STATUS OK')
    
    def handle_init_NOTIFY(self, args, ids):
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
                if action == "TRUE":
                    return self.factory.addNotifier((host, port)
                    ).addCallback(self.notifyFinish)
                elif action == "FALSE":
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
        self.sendLine("NOTIFY %s" % msg)
    # The RESET, KILL and DISCONNECT commands
    
    def handle_RESET(self, args, ids):
        self.sendLine('RESET OK')
        self._reset()
        return self.factory.reset(ids)
    
    def handle_KILL(self, args, ids):
        self.sendLine('KILL OK')
        self._reset()
        return self.factory.kill(ids)
    
    def handle_DISCONNECT(self, args, ids):
        log.msg("Disconnecting client...")
        self.sendLine("DISCONNECT OK")
        self.transport.loseConnection()
    

class IControlFactory(Interface):
    """interface to clients for controller"""
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, ids='all'):
        """Cleans out pending commands in an engine's queue."""
    
    #IEngine multiplexer methods
    def execute(self, lines, ids='all'):
        """Execute lines of Python code."""
    
    def push(self, key, value, ids='all'):
        """Put value into locals namespace with name key."""
    
    def pushPickle(self, key, package, ids='all'):
        """Unpickle package and put into the locals namespace with name key."""
    
    def pull(self, key, ids='all'):
        """Gets an item out of the self.locals dict by key."""
    
    def pullPickle(self, key, ids='all'):
        """Gets an item out of the self.locals dist by key and pickles it."""
    
    def update(self, dictOfData, ids='all'):
        """Updates the self.locals dict with the dictOfData."""
    
    def updatePickle(self, dictPickle, ids='all'):
        """Updates the self.locals dict with the pickled dict."""
    
    def status(self, ids='all'):
        """status of engines"""
    
    def reset(self, ids='all'):
        """Reset the InteractiveShell."""
    
    def kill(self, ids='all'):
        """kill engines"""
    
    def getCommand(self, i=None, ids='all'):
        """Get the stdin/stdout/stderr of command i."""
    
    def getLastCommandIndex(self, ids='all'):
        """Get the index of the last command."""
    


class ControlFactoryFromService(protocol.ServerFactory):
    """the controller factory"""
    
    implements(IControlFactory)
    
    protocol = ControlTCPProtocol
    
    def __init__(self, service):
        self.service = service
    
    def addNotifier(self, n):
        return self.service.addNotifier(n)
    
    def delNotifier(self, n):
        return self.service.delNotifier(n)
    
    def verifyIds(self, ids):
        return self.service.verifyIds(ids)
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, ids='all'):
        """Cleans out pending commands in an engine's queue."""
        return self.service.cleanQueue(ids)
    
    #IEngine multiplexer methods
    def execute(self, lines, ids='all'):
        """Execute lines of Python code."""
        return self.service.execute(lines, ids)
    
    def push(self, key, value, ids='all'):
        """Put value into locals namespace with name key."""
        return self.service.put(key, value, ids)
    
    def pushPickle(self, key, value, ids='all'):
        """Put value into locals namespace with name key."""
        return self.service.putPickle(key, value, ids)
    
    def pull(self, key, ids='all'):
        """Gets an item out of the self.locals dict by key."""
        return self.service.get(key, ids)
    
    def pullPickle(self, key, ids='all'):
        """Gets an item out of the self.locals dict by key."""
        return self.service.getPickle(key, ids)
    
    def update(self, dictOfData, ids='all'):
        """Updates the self.locals dict with the dictOfData."""
        return self.service.update(dictOfData, ids)
    
    def updatePickle(self, dictOfData, ids='all'):
        """Updates the self.locals dict with the dictOfData."""
        return self.service.updatePickle(dictOfData, ids)
    
    def status(self, ids='all'):
        """status of engines"""
        return self.service.status(ids)
    
    def reset(self, ids='all'):
        """Reset the InteractiveShell."""
        return self.service.reset(ids)
    
    def kill(self, ids='all'):
        """kill an engine"""
        return self.service.kill(ids)
    
    def getCommand(self, i=None, ids='all'):
        """Get the stdin/stdout/stderr of command i."""
        return self.service.getCommand(i, ids)
    
    def getLastCommandIndex(self, ids='all'):
        """Get the index of the last command."""
        return self.service.getLastCommandIndex(ids)
    


components.registerAdapter(ControlFactoryFromService,
                        controllerservice.ControllerService,
                        IControlFactory)
