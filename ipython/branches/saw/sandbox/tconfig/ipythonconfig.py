"""Toy example of a TConfig-based configuration description.
"""

import enthought.traits.api as T

# For interactive testing
import tconfig; reload(tconfig)
from tconfig import TConfig


class IPythonConfig(TConfig):
    """Class Docstring

    More

    And more...
    """

    m = T.Int(123)

    select = T.Trait('only','one','of','these')
    
    class InitOnly(TConfig):
        """
        The Read-only part of the configuration.

        More than one line of info...
        """
        n = T.Int
        x = T.Float

    class Protocol(TConfig):
        """Specify the Protocol

        More text...
        """
        include = T.Str
        ptype = T.Str

        class Handler(TConfig):
            """Specify the handler, a string.

            More..."""
            key = T.Str
            key2 = T.Str

    class Machine(TConfig):
        """Set the machine by ip address and port number."""
        ip = T.Str
        port = T.Int
