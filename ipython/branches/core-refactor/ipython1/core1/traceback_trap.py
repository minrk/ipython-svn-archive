""" Object to manage sys.excepthook().
"""

# Standard library imports.
import sys


class TracebackTrap(object):
    """ Object to trap and format tracebacks.
    """

    def __init__(self, formatters=None):
        # A list of formatters to apply.
        if formatters is None:
            formatters = []
        self.formatters = formatters

        # All of the traceback information provided to sys.excepthook().
        self.args = None

        # The previous hook before we replace it.
        self.old_hook = None


    def hook(self, *args):
        """ This method actually implements the hook.
        """

        self.args = args

    def set(self):
        """ Set the hook.
        """

        if sys.excepthook is not self.hook:
            self.old_hook = sys.excepthook
            sys.excepthook = self.hook

    def unset(self):
        """ Unset the hook.
        """

        sys.excepthook = self.old_hook

    def clear(self):
        """ Remove the stored traceback.
        """

        self.args = None

    def add_to_message(self, message):
        """ Add the formatted display of the traceback to the message dictionary
        being returned from the interpreter to its listeners.

        Parameters
        ----------
        message : dict
        """

        # If there was no traceback, then don't add anything.
        if self.args is None:
            return

        # Go through the list of formatters and let them add their formatting.
        traceback = {}
        for formatter in self.formatters:
            traceback[formatter.identifier] = formatter(*self.args)
        
        message['traceback'] = traceback

