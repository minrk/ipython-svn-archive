"""Toy example of a TConfig-based configuration description."""

import enthought.traits.api as T
from tconfig import TConfig

# This is the class declaration for the configuration:

class SimpleConfig(TConfig):
    """Configuration for my application."""

    datafile = T.Str('data.txt')
    solver = T.Trait('Direct','Iterative')

    class Protocol(TConfig):
        """Specify the Protocol"""

        ptype = T.Trait('http','ftp','ssh')
        max_users = T.Int(1)
