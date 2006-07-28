
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

from twisted.internet import protocol, defer, reactor
from twisted.protocols import basic
from twisted.python import components, log

from zope.interface import Interface, implements

from ipython1.kernel import controllerservice

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
    
    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self.state = 'init'
        self.work_vars = {}
    
    def lineReceived(self, line):
        split_line = line.split(" ", 1)
        if len(split_line) == 1:
            cmd = split_line[0]
            args = None
            ids = 'all'
        elif len(split_line) == 2:
            cmd = split_line[0]
            arglist = split_line[1].split('::')
            if len(arglist) > 1:
                ids = self.parseids(arglist[1:])
            else:
                ids = 'all'
            args = arglist[0]
        
        if not self.factory.verifyIds(ids):
            self.sendLine("BAD")
            self.state = 'init'
            self.reset_work_vars()
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
                self.reset_work_vars()
    
    # Copied from twisted.mail.imap4
    def rawDataReceived(self, data):
        passon = self._pendingLiteral.write(data)
        if passon is not None:
            self.setLineMode(passon) # should I reset the state here?
    
    def reset_work_vars(self):
        self.work_vars = {}
    
    def _reset(self):
        self.work_vars = {}
        self.state = 'init'
    
    def parseids(self, idsList):
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
            self.push_finish("FAIL")
            return
        else:
            args_str = args

        self.work_vars['push_name'] = args_str
        self.work_vars['push_ids'] = ids
        # Setup to process the command
        self.state = 'pushing'
    
    def setup_literal(self, size):
        """Called by data command handlers."""
        d = defer.Deferred()
        self._pendingLiteral = LiteralString(size, d)
        self.setRawMode()
        return d        
    
    def push_finish(self,msg):
        self.sendLine("PUSH %s" % msg)
        self._reset()
    
    def handle_pushing_PICKLE(self, size_str, ids):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.push_finish("FAIL")
        else:         
            d = self.setup_literal(size)
            d.addCallback(self.put_pickle)
    
    def put_pickle(self, package):
        try:
            data = pickle.loads(package)
        except pickle.PickleError:
            self.push_finish("FAIL")
        else:
            # What if this fails?  When could it?
            self.factory.pushPickle(self.work_vars['push_name'],
                package, self.work_vars['push_ids'])
            self.push_finish("OK")
    
    #####   
    ##### The UPDATE command
    #####
    
    def handle_init_UPDATE(self, args, ids):
        
        # Parse the args
        if not args:
            self.update_finish("FAIL")
            return
        else:
            args_str = args

        self.work_vars['update_dict'] = args_str
        self.work_vars['push_ids'] = ids
        # Setup to process the command
        self.state = 'updating'
    
    def setup_literal(self, size):
        """Called by data command handlers."""
        d = defer.Deferred()
        self._pendingLiteral = LiteralString(size, d)
        self.setRawMode()
        return d        
    
    def update_finish(self,msg):
        self.sendLine("UPDATE %s" % msg)
        self._reset()
    
    def handle_updating_PICKLE(self, size_str, ids):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.update_finish("FAIL")
        else:         
            d = self.setup_literal(size)
            d.addCallback(self.update_pickle)
    
    def update_pickle(self, package):
        try:
            data = pickle.loads(package)
        except pickle.PickleError:
            self.update_finish("FAIL")
        else:
            # What if this fails?  When could it?
            self.factory.updatePickle(self.work_vars['update_name'],
                package, self.work_vars['update_ids'])
            self.update_finish("OK")
    
    #####
    ##### The PULL command
    #####
    
    def handle_init_PULL(self, args, ids):
        
        # Parse the args
        if not args:
            self.pull_finish("FAIL")
            return
        else:
            pull_name = args
            
        self.work_vars['pull_type'] = 'PICKLE'
        d = self.factory.pullPickle(pull_name, ids)
                
        d.addCallback(self.pull_ok)
        d.addErrback(self.pull_fail)
    
    def pull_ok(self, resultList):
        # Add error code here and chain the callbacks
        try:
            result = map(pickle.loads,resultList)
            presult = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.pull_finish("FAIL")
        else:
            self.sendLine("PICKLE %s" % len(presult))
            self.transport.write(presult)
            self.pull_finish("OK")
    
    def pull_fail(self, failure):
        self.pull_finish("FAIL")
    
    def pull_finish(self, msg):
        self.sendLine("PULL %s" % msg)
        self._reset()
    
    #####
    ##### The EXECUTE command
    #####
    
    def handle_init_EXECUTE(self, args, ids):
        """Handle the EXECUTE command."""
                
        # Parse the args
        if not args:
            self.execute_finish("FAIL")
            return
            
        if "BLOCK" in args:
            block = True
            execute_cmd = args[6:]
        else:
            block = False
            execute_cmd = args
        
        if not execute_cmd:
            self.execute_finish("FAIL")
            return
        
        if block:
            d = self.factory.execute(execute_cmd, ids)
            d.addCallback(self.execute_ok_block)
        else:                   
            self.execute_finish("OK")   
            d = self.factory.execute(execute_cmd, ids)
        d.addErrback(self.execute_fail)
        return d
    
    def execute_ok_block(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.execute_finish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.execute_finish("OK")
    
    def execute_fail(self, f):
        self.execute_finish("FAIL")
    
    def execute_finish(self, msg):
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
        d.addCallbacks(self.getCommand_ok, self.getCommand_fail)
    
    def getCommand_ok(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.getCommand_finish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.getCommand_finish("OK")
    
    def getCommand_fail(self, f):
        self.getCommand_finish("FAIL")
    
    def getCommand_finish(self, msg):
        self.sendLine("GETCOMMAND %s" %msg)
    
    
    #####
    ##### GETLASTCOMMANDINDEX command
    #####
    
    def handle_init_GETLASTCOMMANDINDEX(self, args, ids):
        
        d = self.factory.getLastCommandIndex(ids)
        d.addCallbacks(self.getLastCommandIndex_ok, self.getLastCommandIndex_fail)
    
    def getLastCommandIndex_ok(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.getLastCommandIndex_finish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.getLastCommandIndex_finish("OK")
    
    def getLastCommandIndex_fail(self, f):
        self.getLastCommandIndex_finish("FAIL")
    
    def getLastCommandIndex_finish(self, msg):
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
            self.sendLine('NOTIFY FAIL')
            return
        else:
            args_split = args.split(" ")
        
        if len(args_split) == 3:
            action, host, port = args_split
            try:
                port = int(port)
            except (ValueError, TypeError):
                self.sendLine("NOTIFY FAIL")
            else:
                if action == "TRUE":
                    self.factory.add_notifier((host, port))
                    self.sendLine('NOTIFY OK')
                elif action == "FALSE":
                    self.factory.del_notifier((host, port))
                    self.sendLine('NOTIFY OK')
                else:
                    self.sendLine('NOTIFY FAIL')
        else:
            self.sendLine('NOTIFY FAIL')
    
    # The RESET, KILL and DISCONNECT commands
    
    def handle_RESET(self, args, ids):
        self.factory.reset(ids)
        self.sendLine('RESET OK')
        self._reset()
    
    def handle_KILL(self, args, ids):
        return self.factory.kill(ids).addErrback(lambda _: 7)
    
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
    
    def add_notifier(self, n):
        return self.service.addNotifier(n)
    
    def del_notifier(self, n):
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
