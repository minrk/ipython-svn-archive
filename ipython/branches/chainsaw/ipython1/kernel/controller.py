
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

from twisted.internet import protocol, defer
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
    

class ResultReporterProtocol(protocol.DatagramProtocol):
    
    def __init__(self, result, addr):
        self.result = result
        self.addr = addr
    
    def startProtocol(self):
        package = pickle.dumps(self.result, 2)
        self.transport.write("RESULT %i %s" % (len(package), package), 
            self.addr)
        self.tried = True
    
    def datagramReceived(self,data, sending_addr):
        if sending_addr == self.addr and data == "RESULT OK":
            self.transport.stopListening()
    


class ControlTCPProtocol(basic.LineReceiver):
    
    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self.state = 'init'
        self.work_vars = {}
        peer = self.transport.getPeer()
#        if not self.factory.is_allowed(peer.host):
#            log.msg("Denied Client: %s" % peer.host)
#            self.transport.loseConnection()
    
    def lineReceived(self, line):
        split_line = line.split(" ", 1)
        print split_line
        if len(split_line) == 1:
            cmd = split_line[0]
            args = None
        elif len(split_line) == 2:
            cmd = split_line[0]
            args = split_line[1]
            
        f = getattr(self, 'handle_%s_%s' %
                    (self.state, cmd), None)            
        if f:
            # Handler resolved with state and cmd 
            f(args)
        else:
            f = getattr(self, 'handle_%s' %
                (cmd), None)
            if f:
                # Handler resolved with only cmd
                f(args)
            else:
                f = getattr(self, 'handle_%s' %
                    (self.state), None)
                if f:
                    # Handler resolve with only self.state
                    # Pass the entire line rather than just args
                    f(line)
                else:
                    # No handler resolved
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
    
    #####   
    ##### The PUSH command
    #####
    
    def parseID(self, idList):
        if len(idList) is 0:
            return 'all'
        else:
            try:
                return map(int, idList)
            except:
                return 'all'
    
    def handle_init_PUSH(self, args):
        
        # Parse the args
        if not args:
            self.push_finish("FAIL")
            return
        else:
            argsList = args.split('::')
                                            
        args_str = argsList[0]
        if len(argsList) > 1:
            id = self.parseID(argsList[1:])
        else:
            id = 'all'

        if 'FORWARD' in args_str:
            self.work_vars['push_forward'] = True
            args_str.replace("FORWARD ","")
        else:
            self.work_vars['push_forward'] = False
        
        self.work_vars['push_name'] = args_str
        self.work_vars['push_id'] = id
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
    
    def handle_pushing_PICKLE(self, size_str):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.push_finish("FAIL")
        else:         
            d = self.setup_literal(size)
            d.addCallback(self.process_pickle)
    
    def process_pickle(self, package):
        try:
            data = pickle.loads(package)
        except pickle.PickleError:
            self.push_finish("FAIL")
        else:
            # What if this fails?  When could it?
            self.factory.push(self.work_vars['push_name'],
                data, self.work_vars['push_id'])
            self.push_finish("OK")
    
    #####
    ##### The PULL command
    #####
    
    def handle_init_PULL(self, args):
        
        # Parse the args
        if not args:
            self.pull_finish("FAIL")
            return
        else:
            args_list = args.split("::")
            
        pull_name = args_list[0]
        if len(args_list) is not 0:
            id = self.parseID(args_list[1:])
        else:
            id = 'all'
        self.work_vars['pull_type'] = 'PICKLE'
        d = self.factory.pull(pull_name, id)
                
        d.addCallback(self.pull_ok)
        d.addErrback(self.pull_fail)
    
    def pull_ok(self, result):
        # Add error code here and chain the callbacks
        try:
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
    ##### The RESULT command
    #####
    
    def handle_init_RESULT(self, args):
        
        if args is None:
            d = self.factory.get_last_result()
        else:
            try:
                cmd_num = int(args)
            except (ValueError, TypeError):
                self.result_finish("FAIL")
                return
            else:
                d = self.factory.get_result(cmd_num)
                                
        d.addCallback(self.result_ok)
        d.addErrback(self.result_fail)
    
    def result_ok(self, result):
        # Add error code here and chain the callbacks
        try:
            presult = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.result_finish("FAIL")
        else:
            self.sendLine("PICKLE %s" % len(presult))
            self.transport.write(presult)
            self.result_finish("OK")
    
    def result_fail(self, failure):
        self.result_finish("FAIL")
    
    def result_finish(self, msg):
        self.sendLine("RESULT %s" % msg)
        self._reset()
    
    #####
    ##### The EXECUTE command
    #####
    
    def handle_init_EXECUTE(self, args):
        """Handle the EXECUTE command."""
                
        # Parse the args
        print args
        if not args:
            self.execute_finish("FAIL")
            return
            
        if "BLOCK" in args:
            block = True
            execute_cmd = args[6:]
        else:
            block = False
            execute_cmd = args
        cmdList = execute_cmd.split('::')
        print cmdList
        execute_cmd = cmdList[0]
        id = self.parseID(cmdList[1:])
        
        if not execute_cmd:
            self.execute_finish("FAIL")
            return
        
        d = self.factory.execute(execute_cmd, id)
        d.addErrback(self.execute_fail)
        if block:
            d.addCallback(self.execute_ok_block)
        else:                   
            self.execute_finish("OK")   
            d.addCallback(self.execute_ok)
    
    def execute_ok(self, result):
        for tonotify in self.factory.notifiers():
            reactor.listenUDP(0,ResultReporterProtocol(result, tonotify) )
    
    def execute_ok_block(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.execute_finish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.execute_finish("OK")
            self.execute_ok(result)
    
    def execute_fail(self, f):
        pass
    
    def execute_finish(self, msg):
        self.sendLine("EXECUTE %s" % msg)
        self._reset()
    
    #####
    ##### The MOVE command
    #####
    
    def handle_init_MOVE(self, args):
        """Handle a MOVE commmand."""
        
        print "Moving: ", args
        
        self.work_vars['move_target_addrs'] = []
        self.work_vars['move_failures'] = []            
        
        # Process args
        args_split = args.split(" ", 2)
        if len(args_split) < 3:
            self.finish_move("FAIL")
        # No test is done to see if these are valid python variable names
        self.work_vars['move_source_key'] = args_split[0]
        self.work_vars['move_target_key'] = args_split[1]
        try:
            self.work_vars['move_targets'] = \
                map(int,args_split[2].split(" "))
        except:
            self.move_finish("FAIL")
        else:
            # Lookup the addresses and fail one any don't exist        
            for t in self.work_vars['move_targets']:
                t_addr = self.factory.get_cluster_addr(t)
                if t_addr is None:
                    self.work_vars['move_failures'].append(t)                    
                self.work_vars['move_target_addrs'].append(t_addr)
            if None in self.work_vars['move_target_addrs']:
                self.move_finish("FAIL")
            else: # All addresses are present in the cluster
                print "Targets: ", self.work_vars['move_targets']
                print "Targets: ", self.work_vars['move_target_addrs']                
                d = self.factory.pull(pull_name)
                d.addCallback(self.move_pull_ok)
                d.addErrback(self.move_pull_fail)
    
    def move_pull_ok(self, result):
        # Add error code here and chain the callbacks
        print "move_pull_ok", result
        try:
            self.work_vars['move_pickle'] = pickle.dumps(result, 2)
        except:
            self.move_finish("FAIL")
        else:
            for t in self.work_vars['move_targets']:
                t_addr = self.factory.get_cluster_addr(t)
                c = ClientCreator(reactor, Mover)
                d = c.connectTCP(t_addr[0], t_addr[1])
                d.addCallback(self.move_push)
    
    def move_pull_fail(self, f):
        print f.getTrackback()
        self.move_finish("FAIL")
    
    def move_push(self, proto):
        d = proto.push(self.work_vars['move_target_key'], 
            self.work_vars['move_pickle'])
        
        def handle_move_push(result):
            if result:
                self.move_finish("OK")
            else:
                self.move_finish("FAIL")
        
        d.addCallback(handle_move_push)
    
    def move_push(self):
        pass
    
    def move_finish(self, msg):
        flist = map(str, self.work_vars['move_failures'])
        fstr = " ".join(flist)
        self.sendLine("MOVE %s %s" % (msg, fstr))
        self._reset()
    
    
    #####
    ##### Kernel control commands
    #####
    
    def handle_init_STATUS(self, args):
        
        status = self.factory.status()
        result = (status, self.state)    
                
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.sendLine('STATUS FAIL')
        else:
            self.sendLine("PICKLE %s" % len(package))
            self.transport.write(package)
            self.sendLine('STATUS OK')
    
    def handle_init_ALLOW(self, args):
        args_split = args.split(" ")
        if len(args_split) == 2:
            action, host = args_split
            if action == "TRUE":
                self.factory.allow_client(host)
                self.sendLine('ALLOW OK')
            elif action == "FALSE":
                self.factory.deny_client(host)
                self.sendLine('ALLOW OK')
            else:
                self.sendLine('ALLOW FAIL')
        else:
            self.sendLine('ALLOW FAIL')
    
    def handle_init_NOTIFY(self, args):
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
    
    # The CLUSTER command
    
    def handle_init_CLUSTER(self, args):
        if args == "CLEAR":
            self.factory.clear_cluster()
            self.cluster_finish("OK")
        elif args == "CREATE":
            self.state = 'cluster'
        else:
            self.cluster_finish('FAIL')
    
    def cluster_finish(self,msg):
        self.sendLine("CLUSTER %s" % msg)
        self._reset()
    
    def handle_cluster_PICKLE(self, size_str):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.cluster_finish("FAIL")
        else:         
            d = self.setup_literal(size)
            d.addCallback(self.cluster_process_pickle)
    
    def cluster_process_pickle(self, package):
        try:
            data = pickle.loads(package)
        except pickle.PickleError:
            self.cluster_finish("FAIL")
        else:
            self.factory.create_cluster(data)
            self.cluster_finish("OK")        
    
    # The RESET, KILL and DISCONNECT commands
    
    def handle_RESET(self, args):
        log.msg("Resettng the kernel...")
        self.factory.reset()
        self.sendLine('RESET OK')
        self._reset()
    
    def handle_KILL(self, args):
        log.msg("Killing the kernel...")
        reactor.stop()
    
    def handle_DISCONNECT(self,args):
        log.msg("Disconnecting client...")
        self.sendLine("DISCONNECT OK")
        self.transport.loseConnection()
    

class IControlFactory(Interface):
    """interface to clients for controller"""
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in an engine's queue."""
    
    #IEngine multiplexer methods
    def execute(self, lines, id='all'):
        """Execute lines of Python code."""
    
    def push(self, key, value, id='all'):
        """Put value into locals namespace with name key."""
    
    def pushPickle(self, key, package, id='all'):
        """Unpickle package and put into the locals namespace with name key."""
    
    def pull(self, key, id='all'):
        """Gets an item out of the self.locals dict by key."""
    
    def pullPickle(self, key, id='all'):
        """Gets an item out of the self.locals dist by key and pickles it."""
    
    def update(self, dictOfData, id='all'):
        """Updates the self.locals dict with the dictOfData."""
    
    def updatePickle(self, dictPickle, id='all'):
        """Updates the self.locals dict with the pickled dict."""
    
    def reset(self, id='all'):
        """Reset the InteractiveShell."""
    
    def getCommand(self, i=None, id='all'):
        """Get the stdin/stdout/stderr of command i."""
    
    def getLastCommandIndex(self, id='all'):
        """Get the index of the last command."""
    


class ControlFactoryFromService(protocol.ServerFactory):
    """the controller factory"""
    
    implements(IControlFactory)
    
    protocol = ControlTCPProtocol
    
    def __init__(self, service):
        self.service = service
        self.notifiers = list
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in an engine's queue."""
        return self.service.cleanQueue(id)
    
    #IEngine multiplexer methods
    def execute(self, lines, id='all'):
        """Execute lines of Python code."""
        return self.service.execute(lines, id)
    
    def push(self, key, value, id='all'):
        """Put value into locals namespace with name key."""
        return self.service.put(key, value, id)
    
    def pushPickle(self, key, package, id='all'):
        """Unpickle package and put into the locals namespace with name key."""
        return self.service.putPickle(key, package, id)
    
    def pull(self, key, id='all'):
        """Gets an item out of the self.locals dict by key."""
        return self.service.get(key, id)
    
    def pullPickle(self, key, id='all'):
        """Gets an item out of the self.locals dist by key and pickles it."""
        return self.service.getPickle(key, id)
    
    def update(self, dictOfData, id='all'):
        """Updates the self.locals dict with the dictOfData."""
        return self.service.update(dictOfData, id)
    
    def updatePickle(self, dictPickle, id='all'):
        """Updates the self.locals dict with the pickled dict."""
        return self.service.updatePickle(dictPickle, id)
    
    def reset(self, id='all'):
        """Reset the InteractiveShell."""
        return self.service.reset(id)
    
    def getCommand(self, i=None, id='all'):
        """Get the stdin/stdout/stderr of command i."""
        return self.service.getCommand(i, id)
    
    def getLastCommandIndex(self, id='all'):
        """Get the index of the last command."""
        return self.service.getLastCommandIndex(id)
    


components.registerAdapter(ControlFactoryFromService,
                        controllerservice.ControllerService,
                        IControlFactory)
