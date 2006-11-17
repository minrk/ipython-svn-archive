from twisted.python import log
from twisted.internet import reactor
from twisted.spread import pb

from ipython1.kernel import controllerpb #for IMulti adapter
from ipython1.kernel.controllerservice import IMultiEngine
from ipython1.kernel.util import printer



class Task(object):
    def __init__(self, command, *keys):
        self.command = command
        self.keys = keys
    
    def run():
        self.multiEngine.execute()
        
class TaskManager(object):
    
    def __init__(self, addr):
        self.addr = addr
        
    def run(self):
        self.clientFactory = pb.PBClientFactory()
        d = self.clientFactory.getRootObject()
        d.addCallback(self._gotRoot)
        log.startLogging(sys.stdout)
        reactor.connectTCP(self.addr[0], self.addr[1], self.clientFactory)
        reactor.run()
        
    def _gotRoot(self, rootObj):
        self.multiEngine = IMultiEngine(rootObj)
        self._runTasks()
        
    def _runTasks(self):
        
    def newTask(self, command, *keys):
        t = Task(command, keys)
        t.multiEngine = self.multiEngine
        

def main():
    tm = TaskManager(('127.0.0.1', 11111))
    t0 = tm.new('a = 10', 'a')
    d0 = t0.run()
    
    
if __name__ == '__main__':
    main()

