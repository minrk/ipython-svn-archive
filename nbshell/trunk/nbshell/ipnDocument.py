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

import os

import wx
from lxml import etree

from notabene import notebook 

from nbshell import IPythonLog
from nbshell import Sheet
from nbshell.utils import *

class ipnDocument(object):
    def __init__(self, app, notebookview):
        
        self.notebook = None # the notebook object
        self.logs = None # a dictionary of the logs
        self.sheet = None # The sheet object
        self.view = notebookview
        self.app = app
        self.factory = self.app.plugin_dict
        #self.celllist = [] 
        self.fileinfo = { # contains various information of the file
                           # currently being edited
            "init":False, # This must be True when the
                           # structure is initialized
            "path":None,   # The path to the file
            "name":None,   # The name of the file.
            "script":None, # Is the file a script. If so here is the
                           # first line of the file to be copied when
                           # the file is saved
            "modified":False, # If true the file has been modified after the last save
            "untitled":False # This is set True by DefaultNotebook() and False by LoadFile()
            }
        self.Clear() #Sets logs, sheet

    def DefaultNotebook(self):
        """Create a default empty notebook"""
        self.Clear()
        self.notebook = notebook.Notebook('untitled.nbk')
        #etree.dump(self.notebook.root) #dbg
        self.logs = {'default-log':IPythonLog.IPythonLog(self, self.notebook, 'default-log')}
        etree.SubElement(self.notebook.root, 'sheet', format='rest')
        self.sheet = Sheet.Sheet(self, self.notebook, self.view, self.factory)
        self.fileinfo['init'] = True
        self.fileinfo['path'] = os.getcwd()
        self.fileinfo['name'] = 'untitled.nbk'
        self.fileinfo['modified'] = False
        self.fileinfo['untitled'] = True
        self.sheet.DefaultSheet()
        self.SetSavePoint()
        
    def Clear(self):
        """Clears the document. Does not ask for confirmation. Clear does not
        create a viewable notebook. You should call DefaultNotebook instead"""
        self.fileinfo["init"] = False
        
        #Call self.sheet.Clear to update the view
        if self.sheet is not None:
            self.sheet.Clear()
        self.notebook = None
        self.logs = {}
        self.sheet = None
        self.fileinfo['untitled'] = True

    def LoadFile(self, filename, overwrite = False):
        """Loads the file with the given filename. If there is currently a
        modified file in the document and overwrite is False, returns False
        and does nothing. If some error ocurred throws an exception. If
        everything is OK returns True. The UI should call this method"""

        #1. Is the previous document modified?
        if self.fileinfo["init"] and self.fileinfo["modified"] and not overwrite:
            return False
        self.Clear()
        
        #2. Create the notebook, log, sheet objects
        try:
            self.notebook = notebook.Notebook.from_file(filename)
            # Set up the fileinfo structure
            import os
            self.fileinfo["init"] = True
            self.fileinfo['path'], self.fileinfo["name"] = os.path.split(filename)
            if self.fileinfo['path'] == '':
                self.fileinfo['path'] = os.getcwd()
            self.fileinfo["modified"] = False
            self.fileinfo['untitled'] = False

            logids = self.notebook.root.xpath('//ipython-log/@id')
            self.logs = dict((x, IPythonLog.IPythonLog(self,self.notebook,x)) for x in logids)
            # Append an empty cell at the end of each log
            [self.logs[x].SetLastInput() for x in self.logs]
            self.sheet = Sheet.Sheet(self, self.notebook, self.view, self.factory)
            # append the empty inputs in the sheet
            self.sheet.Update(update = False, celllist = True, dicts = True)
            self.sheet.SetLastInputs(update = False)
            self.sheet.Update(update = True)
            #etree.dump(self.notebook.root) #dbg
            #Set the current cell and position
        except:
            #self.Clear() #TODO: This does not work well if an exception occured. 
            raise
        
        #3. Update the sheet. 
        self.SetSavePoint() 
        return True
    
    def IsModified(self):
        """returns if the file has been modified since last save"""
        return default(lambda:self.sheet.modified,False)
    
    def SetSavePoint(self):
        """ Sets the save point of the document. It is used to determine if
        the document was modified after the last save"""
        self.sheet.SetSavePoint()

    def SaveFile(self, filename = None):
        """Saves the file. If filename is given use this as a file name and
        change self.fileinfo['name']. If filename is None use
        self.fileinfo['name']. If the file is saved successfully return True.
        If there are problems opening the file throws an exception. """

        if filename is None:
            #print 'fileinfo -> %s'%str(self.fileinfo) #dbg
            if (not self.fileinfo['init']) or self.fileinfo['name'] is None:
                raise Exception
            else:
                filename = self.fileinfo['path'] +'/' + self.fileinfo['name']
        mod = self.fileinfo['modified']
        try:
            # delete the last inputs in the sheet
            self.sheet.ClearLastInputs()
            # delete the last empty cell in the logs
            [self.logs[x].ClearLastInput() for x in self.logs]

            #update the data from the views and create the <sheet> element
            self.sheet.UpdateDoc()
            #print 'root-> %s'%str(self.notebook.root) #dbg
            #etree.dump(self.notebook.root) #dbg
            #. write to the file
            self.notebook.write(filename)
            #. set the last inputs again
            [self.logs[x].SetLastInput() for x in self.logs]
            self.sheet.SetLastInputs()
        except:
            self.fileinfo['modified'] = mod
            raise
        self.fileinfo['path'], self.fileinfo['name'] = os.path.split(filename)
        if self.fileinfo['path'] == '':
            self.fileinfo['path'] = os.getcwd()
        self.fileinfo['modified'] = False
        self.SetSavePoint()

    def Rerun(self):
        """Reruns all logs"""
        for key in self.logs:
            self.logs[key].Reset()
            self.logs[key].Run(0)
        #Update the sheet without recreating the celllist
        #print "The rerun notebook" #dbg
        #etree.dump(self.notebook.root) #dbg
        self.sheet.Update(update = True, output = True)
        
    def Export(self, filename = None, format = 'html'):
        """Exports the notebook to a file of the given format. If filename is
        None use the notebook filename. Returns the exported filename"""
        self.sheet.UpdateDoc()
        self.sheet.ClearLastInputs()
        result = self.notebook.write_formatted(filename, format)
        self.sheet.SetLastInputs()
        return result
        
