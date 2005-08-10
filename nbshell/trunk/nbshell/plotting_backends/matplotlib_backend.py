"""matplotlib_backend.py - Classes needed to use Matplotlib in nbshell"""

#*****************************************************************************
#       Copyright (C) 2005 Tzanko Matev. <tsanko@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from nbshell import Release
__author__  = '%s <%s>' % Release.author
__license__ = Release.license
__version__ = Release.version

from nbshell.plotting_backends import backend_base

class PlotLibraryInterface(backend_base.PlotLibraryInterface):
    def __init__(self, filename_iter):
        self.filename_iter = filename_iter
    def grab_png(self, caption = None):
        """Exports a png figure"""
        from matplotlib import _pylab_helpers as __pylab_helpers
        figmanager = __pylab_helpers.Gcf.get_active()
        if figmanager is None:
            del(__pylab_helpers)
            return None
        else:
            from matplotlib import pylab as __pylab
            filename = self.filename_iter.next()
            __pylab.savefig(filename, dpi=50)
            __pylab.close()
            del(__pylab_helpers)
            del(__pylab)
            if caption is None:
                cap_str = ''
            else:
                cap_str = 'caption = "%s"'%str(caption)
            xml = '<ipython-figure type="png" filename="%s" %s/>'%\
                (filename, cap_str)
            return xml
