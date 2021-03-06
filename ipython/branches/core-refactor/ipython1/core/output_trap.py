""" Trap stdout/stderr.
"""

# Standard library imports.
import sys
from cStringIO import StringIO


class OutputTrap(object):
    """ Object which can trap text sent to stdout and stderr.
    """

    def __init__(self):
        # Filelike objects to store stdout/stderr text.
        self.out = StringIO()
        self.err = StringIO()

        # Boolean to check if the stdout/stderr hook is set.
        self.out_set = False
        self.err_set = False

    @property
    def out_text(self):
        """ Return the text currently in the stdout buffer.
        """
        return self.out.getvalue()

    @property
    def err_text(self):
        """ Return the text currently in the stderr buffer.
        """
        return self.err.getvalue()

    def set(self):
        """ Set the hooks.
        """

        if sys.stdout is not self.out:
            self._out_save = sys.stdout
            sys.stdout = self.out
            self.out_set = True

        if sys.stderr is not self.err:
            self._err_save = sys.stderr
            sys.stderr = self.err
            self.err_set = True

    def unset(self):
        """ Remove the hooks.
        """

        sys.stdout = self._out_save
        self.out_set = False

        sys.stderr = self._err_save
        self.err_set = False

    def clear(self):
        """ Clear out the buffers.
        """

        self.out.close()
        self.out = StringIO()

        self.err.close()
        self.err = StringIO()

    def add_to_message(self, message):
        """ Add the text from stdout and stderr to the message from the
        interpreter to its listeners.

        Parameters
        ----------
        message : dict
        """

        out_text = self.out_text
        if out_text:
            message['stdout'] = out_text

        err_text = self.err_text
        if err_text:
            message['stderr'] = err_text



