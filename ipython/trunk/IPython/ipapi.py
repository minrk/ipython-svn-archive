''' IPython customization API

Your one-stop module for configuring & extending ipython

The API will probably break when ipython 1.0 is released, but so 
will the other configuration method (rc files).

All names prefixed by underscores are for internal use, not part 
of the public api.

Below is an example that you can just put to a module and import from ipython. 

A good practice is to install the config script below as e.g. 

~/.ipython/my_private_conf.py

And do 

import_mod my_private_conf 

in ~/.ipython/ipythonrc

That way the module is imported at startup and you can have all your
personal configuration (as opposed to boilerplate ipythonrc-PROFILENAME 
stuff) in there. 

-----------------------------------------------
import IPython.ipapi
ip = IPython.ipapi.get()

def ankka_f(self, arg):
    print "Ankka",self,"says uppercase:",arg.upper()

ip.expose_magic("ankka",ankka_f)

ip.magic('alias sayhi echo "Testing, hi ok"')
ip.magic('alias helloworld echo "Hello world"')
ip.system('pwd')

ip.ex('import re')
ip.ex("""
def funcci(a,b):
    print a+b
print funcci(3,4)
""")
ip.ex("funcci(348,9)")

def jed_editor(self,filename, linenum=None):
    print "Calling my own editor, jed ... via hook!"
    import os
    if linenum is None: linenum = 0
    os.system('jed +%d %s' % (linenum, filename))
    print "exiting jed"

ip.set_hook('editor',jed_editor)

o = ip.options
o.autocall = 2  # FULL autocall mode

print "done!"
'''

# stdlib imports
import sys

# our own
from IPython.genutils import warn,error
 
class TryNext(Exception):
    """Try next hook exception.
     
    Raise this in your hook function to indicate that the next hook handler
    should be used to handle the operation.  If you pass arguments to the
    constructor those arguments will be used by the next hook instead of the
    original ones.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

# contains the most recently instantiated IPApi

class IPythonNotRunning:
    """Dummy do-nothing class.

    Instances of this class return a dummy attribute on all accesses, which
    can be called and warns.  This makes it easier to write scripts which use
    the ipapi.get() object for informational purposes to operate both with and
    without ipython.  Obviously code which uses the ipython object for
    computations will not work, but this allows a wider range of code to
    transparently work whether ipython is being used or not."""
    
    def __str__(self):
        return "<IPythonNotRunning>"

    __repr__ = __str__

    def __getattr__(self,name):
        return self.dummy

    def dummy(self,*args,**kw):
        """Dummy function, which doesn't do anything but warn."""
        warn("IPython is not running, this is a dummy no-op function")

_recent = None


def get(allow_dummy=False):
    """Get an IPApi object.

    If allow_dummy is true, returns an instance of IPythonNotRunning 
    instead of None if not running under IPython.

    Running this should be the first thing you do when writing extensions that
    can be imported as normal modules. You can then direct all the
    configuration operations against the returned object.
    """
    global _recent
    if allow_dummy and not _recent:
        _recent = IPythonNotRunning()
    return _recent

class IPApi:
    """ The actual API class for configuring IPython 
    
    You should do all of the IPython configuration by getting an IPApi object
    with IPython.ipapi.get() and using the attributes and methods of the
    returned object."""
    
    def __init__(self,ip):
        
        # All attributes exposed here are considered to be the public API of
        # IPython.  As needs dictate, some of these may be wrapped as
        # properties.

        self.magic = ip.ipmagic
        
        self.system = ip.ipsystem
        
        self.set_hook = ip.set_hook
        
        self.set_custom_exc = ip.set_custom_exc

        self.user_ns = ip.user_ns

        # Session-specific data store, which can be used to store
        # data that should persist through the ipython session.
        self.meta =  ip.meta
    
        # The ipython instance provided
        self.IP = ip

        global _recent
        _recent = self

    # Use a property for some things which are added to the instance very
    # late.  I don't have time right now to disentangle the initialization
    # order issues, so a property lets us delay item extraction while
    # providing a normal attribute API.
    def get_db(self):
        """A handle to persistent dict-like database (a PickleShareDB object)"""
        return self.IP.db

    db = property(get_db,None,None,get_db.__doc__)

    def get_options(self):
        """All configurable variables."""
        return self.IP.rc

    options = property(get_options,None,None,get_options.__doc__)
    
    def expose_magic(self,magicname, func):
        ''' Expose own function as magic function for ipython 
    
        def foo_impl(self,parameter_s=''):
            """My very own magic!. (Use docstrings, IPython reads them)."""
            print 'Magic function. Passed parameter is between < >: <'+parameter_s+'>'
            print 'The self object is:',self
    
        ipapi.expose_magic("foo",foo_impl)
        '''
                
        import new
        im = new.instancemethod(func,self.IP, self.IP.__class__)
        setattr(self.IP, "magic_" + magicname, im)
    
    def ex(self,cmd):
        """ Execute a normal python statement in user namespace """
        exec cmd in self.user_ns
    
    def ev(self,expr):
        """ Evaluate python expression expr in user namespace 
        
        Returns the result of evaluation"""
        return eval(expr,self.user_ns)
    
    def runlines(self,lines):
        """ Run the specified lines in interpreter, honoring ipython directives.
        
        This allows %magic and !shell escape notations.
        
        Takes either all lines in one string or list of lines.
        """
        if isinstance(lines,basestring):
            self.IP.runlines(lines)
        else:
            self.IP.runlines('\n'.join(lines))

    def to_user_ns(self,*vars):
        """Inject a group of variables into the IPython user namespace.

        Inputs:

         - *vars: one or more variables from the caller's namespace to be put
         into the interactive IPython namespace.  The arguments can be given
         in one of two forms, but ALL arguments must follow the same
         convention (the first is checked and the rest are assumed to follow
         it):
         
           a) All strings, naming variables in the caller.  These names are
           evaluated in the caller's frame and put in, with the same name, in
           the IPython namespace.

           b) Pairs of (name, value), where the name is a string (a valid
           python identifier).  In this case, the value is put into the
           IPython namespace labeled by the given name.  This allows you to
           rename your local variables so they don't collide with other names
           you may already be using globally, or elsewhere and which you also
           want to propagate.


        This utility routine is meant to ease interactive debugging work,
        where you want to easily propagate some internal variable in your code
        up to the interactive namespace for further exploration.

        When you run code via %run, globals in your script become visible at
        the interactive prompt, but this doesn't happen for locals inside your
        own functions and methods.  Yet when debugging, it is common to want
        to explore some internal variables further at the interactive propmt.

        Examples:

        To use this, you first must obtain a handle on the ipython object as
        indicated above, via:

        import IPython.ipapi
        ip = IPython.ipapi.get()

        Once this is done, inside a routine foo() where you want to expose
        variables x and y, you do the following:

        def foo():
            ...
            x = your_computation()
            y = something_else()
            
            # This pushes x and y to the interactive prompt immediately, even
            # if this routine crashes on the next line after:
            ip.to_user_ns('x','y')
            ...
            # return

        The following example shows you how to rename variables to avoid
        clashes:

        def bar():
            ...
            x,y,z,w = foo()
            
            # Push these variables with different names, so they don't
            # overwrite x and y from before
            ip.to_user_ns(('x1',x),('y1',y),('z1',z),('w1',w))
            # which is more conveniently written as:
            ip.to_user_ns(*zip(('x1','y1','z1','w1'),(x,y,z,w)))
            
            ...
            # return """

        # print 'vars given:',vars # dbg
        # Get the caller's frame to evaluate the given names in
        cf = sys._getframe(1)
        
        # XXX fix this after Ville replies...
        user_ns = self.user_ns

        if isinstance(vars[0],basestring):
            # assume that all variables are given as strings
            try:
                for name in vars:
                    user_ns[name] = eval(name,cf.f_globals,cf.f_locals)
            except:
                error('could not get var. %s from %s' %
                      (name,cf.f_code.co_name))

        else:
            # assume they are all given as pairs of name,object
            user_ns.update(dict(vars))


def launch_new_instance(user_ns = None):
    """ Create and start a new ipython instance.
    
    This can be called even without having an already initialized 
    ipython session running.
    
    This is also used as the egg entry point for the 'ipython' script.
    
    """
    ses = create_session(user_ns)
    ses.mainloop()


def create_session(user_ns = None):    
    """ Creates, but does not launch an IPython session.
    
    Later on you can call obj.mainloop() on the returned object.
    
    This should *not* be run when a session exists already.
    
    """
    if user_ns is not None: 
        user_ns["__name__"] = user_ns.get("__name__",'ipy_session')
    import IPython
    return IPython.Shell.start(user_ns = user_ns)
