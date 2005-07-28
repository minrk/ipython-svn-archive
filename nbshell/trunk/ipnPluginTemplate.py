""" Generic editing plugin. It does nothing. Should be used as a reference how
to make editing plugins. TODO: The current plugin design deffers from the one
shown here. """

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

def GetPluginFactory():
    """ Returns the factory object for the plugin. This function is called
    at the start of the program and should be called only once.
    """
    return GenericPluginFactory()

class GenericPluginFactory(object):
    """ This class is responsible for creating the document and view parts of 
    a plugin. Also it has some functions giving information about the plugin.
    The reason this class exists is because the document and view classes of
    the program shouldn't care how plugin objects are created. For example all
    the plain text in the notebook could be contained a single object which is 
    returned every time the document class wants to get a new one."""
    
    string = "generic"
    type = "encoded"
    #def GetString(self):
    #    """ Returns the type string of the plugin. This is used when a notebook
    #    file is loaded. See notebookformat.txt for more info"""
    #    return "generic"
    
    #TODO: remove this
    #def GetType(self):
    #    """ Returns the way data should be passed to the plugin. Currently
    #    supported types are "raw" and "encoded". See notebookformat.txt for 
    #    more info"""
    #    return "encoded" #Probably only the python code plugin should be raw
        
    def CreateDocumentPlugin(self,document, **kwds):
        """Creates the document part of the plugin. The returned object is 
        stored in ipgDocument.celllist and is responsible for storing and
        serialization of data. "**kwds" contain additional arguments for the plugin.
        """
        return GenericDocumentPlugin(document, **kwds)
    
    def CreateViewPlugin(self,docplugin, view):
        """ Creates a view plugin connected to the given document plugin and 
        the given view. The view plugin is responsible for creating windows,
        handling events, etc. In simple plugins the document and the view plugin
        may be the same object
        """
        
        #In the distant future I might need to create views of different type for
        #one doc plugin. For example for a LaTeX plugin I might create a view 
        #for previewing in the notebook widget and a view for editing the LaTeX
        #code in a separate window
        if view.type=="notebook":
            return GenericNotebookViewPlugin(docplugin, view)
        else:
            return None #Well here I should throw an exception, however I am 
                        #not supposed to get to this line for a long long time
#end GenericPluginFactory

#TODO: This class makes no sense with the xml file format. Remove it.
class GenericDocumentPlugin(object):
    """ objects of this class are responsible for storing data, serializing and
    loding data, and updating the view plugins"""
    def __init__(self, document, **kwds):
        """Initialization"""
        #self.LoadData(data)
        self.document = document
        self.view = None    #This plugin is designed for a single view. For
                            #multiple view there should be some modifications
        self.args = ["generic"]
                            
    def Clear(self):
        """Clears all data"""
        self.args = ["generic"]

    def LoadData(self, data=None):
        """Loads data in the object. If "data" is None then clears all data"""
            
        #Your code goes here
        
        #Now update the view
        if(self.view is not None):
            self.view.Update()

    def LoadRaw(self, f, args):
        """ Loads raw data from file 'f'. 'args' is a list of
        arguments read from the file, args[0] is the plugin type. This
        method should be defined when the plugin is of type 'raw'. The
        method must read the lines until it reaches a line with a
        command #@endcell. The method must return the number of lines
        it has read
        """
        self.args = args
        pass

    def LoadEncoded(self,gendata, args):
        """Loads encoded data from file. 'gendata' is a generator
        which yields one decoded line at a time. 'args' is a list of
        arguments, args[0] is the plugin type.
        """
        self.args = args
        pass

    def GetArgs(self):
        """ Returns a list of strings which will be used as the
    arguments of the cell when it is saved. The string with index 0
    should be the type string of the plugin"""
        return self.args

    def Serialize(self, file=None, encodefunc = None):
        """Stores data in file. If the type of the plugin is raw, then
        the "file" parameter contains a file object where data should be
        written. If the type is encoded then the encodefunc parameter contains
        a function which should be called for each line of text which should 
        be serialized
        """
        #how the encoding plugins should serialize data
        # while not more data is left
        #       text = generate_a_line_of_text()
        #       encodefunc(text)
        pass
    
    #def SetView(self, view):
    #    """Set the view for the plugin"""
    #    self.view=view

    def GetFactory(self):
        """Returns a factory instance"""
        return GenericPluginFactory()

class GenericNotebookViewPlugin(object):
    """A generic view plugin. Used for handling data display."""
    def __init__(self, docplugin, view):
        """ Initialization"""
        self.view = view
        self.doc = docplugin
        self.document=docplugin.document
        
    def Update(self):
        """ This method is required for all view implementations. It must
        update the view."""
        pass
        
    def UpdateDoc(self):
        """ This method updates data in the document, from the user input in
        the view """
        pass
    
    def Close(self, update=True):
        """ This method is called when the document cell is
        destroyed. It must close all windows. If update is false, do
        not update the view"""
        pass

    
