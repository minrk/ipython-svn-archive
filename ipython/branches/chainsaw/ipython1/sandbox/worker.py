import threading
import ipython1.kernel1p.kernelclient as kc
import Queue
        
class Worker(threading.Thread):
    """A Threaded Worker for the IPython Kernel.
    
    The important feature is that the result() method takes a timeout
    or can be set to not block if there is not a result ready.  It takes
    the same arguments as Queue.get().
    
    WARNING:  There is currently no way of killing the thread (fperez - there
    is NO way to kill threads in general...)
    
    >>> w = Worker(kernel_addr)
    >>> w.start()
    >>> w.call('f(a,b)',{'a':10,'b':20})   # f must be defined on the kernel
    >>> w.result()
    ('f(a,b)', {'a': 10, 'b': 20}, 2353)
    """

    def __init__(self,addr):
        self.addr = addr
        self.kernel = kc.RemoteKernel(addr)
        self.kernel.connect()
        self.qin = Queue.Queue()
        self.qout = Queue.Queue()
        threading.Thread.__init__(self)
        
    def run(self):
        while True:
            func_or_exp, glob = self.qin.get()
            self.kernel.update(glob)
            self.kernel.execute('result = %s' % func_or_exp)
            result = self.kernel.pull('result')
            self.qout.put((func_or_exp,glob,result))
            
    def call(self, func_or_exp, glob):
        self.qin.put((func_or_exp, glob))
        
    def result(self,block=True,timeout=None):
        return self.qout.get(block=block, timeout=timeout)
