"""backend_base.py - base classes which need to be implemented by a plotting
library"""

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

class PlotLibraryInterface(object):
    """This class must be implemented by all plotting libraries"""
    def __init__(self):
        """Initialization"""
        pass
    
    def get_image_formats(self):
        """This method returns a list of supported image formats. Each image
        format is represented b a string. For each image format the class must
        have an grab_xxx() method where xxx is the given string. Currently
        supported formats: png,null."""
        return ['null','png']
    

    def grab_null(self, caption = None):
        """Each grab_xxx method is executed within the user namespace. It must
        return a xml string, which will be included in the notebook at the
        place where the figure is going to be displayed. grab_null is used for
        testing, it returns an empty string"""
        return ''
    
    def grab_png(self, caption = None):
        """The format for png figures is:
           <ipython-figure type="png" filename="somefile.png" caption = "caption"/>"""
        return "<ipython-figure type=\"png\" filename=\"\" %s/>"%\
               (caption is None and "" or "caption=\"%s\""%str(caption),)

