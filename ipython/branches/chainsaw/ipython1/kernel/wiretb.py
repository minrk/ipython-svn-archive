#!/usr/bin/env python
# encoding: utf-8
"""
wiretb.py

Created by Brian Granger on 2006-08-09.
Copyright (c) 2006 __MyCompanyName__. All rights reserved.
"""

# stdlib imports
import traceback

# third-party imports
from twisted.python.failure import Failure


class WireTraceback(object):
    """Wrap a traceback object in a purely serializable manner.
    
    This class can encapsulate standard exception triplet information, or a Twisted 
    Failure object.
    
    We are not currently using this - eventually we will, but then we will inherit from
    twisted.python.failure.Failure.
    """
    
    def __init__(self, exc_value=None, exc_type=None, exc_tb=None,
                 failure=None):
        """Initialize me with an explanation of the error.
        
        Optional inputs:
        
        - exc_value, exc_type, exc_tb: the standard triplet of exception information.  
        If not provided, they are extracted as usual via sys.exc_info().
        
        - failure(None): if given, it should be an instance of the twisted Failure class, 
        which will be used to construct the traceback information.
        """
        
        # construct from failure object
        if failure is None:
            failure = Failure(exc_value,exc_type,exc_tb)

        # at this point, failure is built and we can use it to get info out of it    
        exc_value, exc_type, exc_tb = failure.value,failure.type,failure.tb
        frames, stack = failure.frames, failure.stack
        
        # We store the pickle-safe part of the exception info
        self.exception = exc_value
        self.exceptionType = exc_type
        
        # make the various forms of tracebacks, which consist purely of strings
        #ptb,ctb,vtb = ultraTB.makeTracebacks(...)
        
        # temporary hack to get a plain traceback, until we fix ultraTB to give us 
        # everything we want
        ftb = traceback.format_tb(exc_tb)
        ptb, ctb, vtb = ftb,ftb,ftb
        # /temp hack
        
        self.contextTB = ctb
        self.plainTB = ptb
        self.verboseTB = vtb
        