# encoding: utf-8
# -*- test-case-name: ipython1.test.test_notebook_xmlutil -*-
"""The XML Representation of Notebook components
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from ipython1.notebook import models, dbutil



# class parseLoader(object):
INPUTS = [">>>", "..."]
TEXT = '"""'
CONTROLS = ["py-section", "py-section-end"]
    
# def __init__(self, user):
#     self.user = user
#     # self.session = session
#     self.sectionStack = []

def control(line):
    if line and line[0] == '#':
        splits = line.split(' ',2)
        if len(splits) > 1:
            if splits[1] in CONTROLS:
                if len(splits) > 2:
                    return splits[1], splits[2]
                else:
                    return splits[1] , ""
        return 'py-comment', line[1:]
    elif line[:3] in INPUTS:
        return 'py-input', line[4:]
    elif line[:3] == TEXT:
        return 'py-text', line[3:]
    return None, line

def readComments(inlines, comments=[]):
    # comments = []
    ctrl, line = control(inlines.pop(0))
    if ctrl == 'py-comment':
        comments.append(line)
    while inlines and ctrl in [None, 'py-comment']: # anything above the first control is ignored
        ctrl, line = control(inlines.pop(0))
        if ctrl == 'py-comment':
            comments.append(line)
    return ctrl, line, comments

def readInput(inlines, inputs=[]):
    # lines = []
    ctrl, line = control(inlines.pop(0))
    while inlines and ctrl == 'py-input': # anything above the first control is ignored
        inputs.append(line)
        ctrl, line = control(inlines.pop(0))
    return ctrl, line, inputs

def readOutput(inlines, outputs=[]):
    # lines = []
    ctrl, line = control(inlines.pop(0))
    while inlines and ctrl is None: # anything above the first control is ignored
        outputs.append(line)
        ctrl, line = control(inlines.pop(0))
    return ctrl, line, outputs

def readText(inlines, textLines=[]):
    line = inlines.pop(0)
    while line[-3:] != TEXT:
        textLines.append(line)
        line = inlines.pop(0)
    textLines.append(line[:-3])
    return textLines


def loadNotebookFromSparse(session, user, s, fname=False):
    """user is a User, and s is either a filename or string.  fname
    is a flag to specify whether s is a filename, defaulting to False."""
    if fname:
        f = open(s)
        s = f.read()
        f.close()
    inlines = s.split('\n')
    sectionStack = []
    ctrl, line, comments = readComments(inlines)
    # while inlines and ctrl in [None, 'py-comment']: # anything above the first control is ignored
    #     ctrl, line = control(inlines.pop(0))
    if ctrl != "py-section":
        nb = dbutil.createNotebook(session, user, "")
        nb.root.comment = '\n'.join(comments)
    else:
        nb = dbutil.createNotebook(session, user, line)
    sectionStack.append(nb.root)
    active = nb.root
    while inlines: # main parsing loop
        if ctrl is None:
            ctrl, line = control(inlines.pop(0))
        elif ctrl == 'py-comment':
            ctrl, line, comments = readComments(inlines, [line])
            if active.comment:
                comments = [active.comment]+comments
            active.comment = '\n'.join(comments)
        elif ctrl == 'py-section':
            active = models.Section(line)
            dbutil.addChild(session, active, sectionStack[-1])
            sectionStack.append(active)
            ctrl, line = control(inlines.pop(0))
        elif ctrl == 'py-section-end':
            sectionStack.pop()
            active = None
            ctrl, line = control(inlines.pop(0))
        elif ctrl == 'py-text':
            active = models.TextCell()
            dbutil.addChild(session, active, sectionStack[-1])
            if line[-3:] == TEXT:
                active.textData = line[:-3]
            else:
                textLines = readText(inlines, [line])
                active.textData = '\n'.join(textLines)
            ctrl, line = control(inlines.pop(0))
        elif ctrl == 'py-input':
            active = models.InputCell()
            dbutil.addChild(session, active, sectionStack[-1])
            ctrl, line, inputs = readInput(inlines, [line])
            active.input = '\n'.join(inputs)
            if ctrl == None:
                ctrl, line, outputs = readOutput(inlines, [line])
                active.output = '\n'.join(outputs)
        else:
            raise "WTF"







