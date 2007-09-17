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
# INPUTS = ["py-input"]
OUTPUT = "#>"
TEXTS = ['"""', "'''"]
CONTROLS = ["py-input", "py-output", "py-section", "py-section-end"]
    
# def __init__(self, user):
#     self.user = user
#     # self.session = session
#     self.sectionStack = []

def control(line):
    if line and line.strip()[0] == '#':
        if line[:2] == OUTPUT:
            return "py-output", line[2:]
        splits = line.split(' ',2)
        if len(splits) > 1:
            if splits[1] in CONTROLS:
                if len(splits) > 2:
                    return splits[1], splits[2]
                else:
                    return splits[1] , ""
        return 'py-comment', line[1:]
    elif line[:3] in TEXTS:
        return line[:3], line[3:]
    return None, line

def readComments(inlines, comments=[]):
    # comments = []
    ctrl, line = control(inlines.pop(0))
    if ctrl == 'py-comment':
        comments.append(line)
    while inlines and (ctrl == 'py-comment' or line == ""):
        ctrl, line = control(inlines.pop(0))
        if ctrl == 'py-comment':
            comments.append(line)
    print "cmt:",comments
    return ctrl, line, comments

def readInput(inlines, inputs=[]):
    ctrl, line = control(inlines.pop(0))
    # print ctrl, line
    while inlines and line[:2] != OUTPUT:
        inputs.append(line)
        line = inlines.pop(0)
        # print line
    print "inp:",inputs, line
    return "py-output", line[2:], inputs

def readOutput(inlines, outputs=[]):
    # lines = []
    ctrl, line = control(inlines.pop(0))
    while inlines and ctrl == "py-output":
        outputs.append(line)
        ctrl, line = control(inlines.pop(0))
    print "out:",outputs
    return ctrl, line, outputs

def readText(inlines, end, textLines=[]):
    line = inlines.pop(0)
    while end not in line:
        textLines.append(line)
        line = inlines.pop(0)
    textLines.append(line[:line.find(end)])
    if line[line.find(end)+3:].strip():
        raise SyntaxError(line)
    return textLines


def loadNotebookFromSparse(session, user, s, fname=False):
    """user is a User, and s is either a filename or string.  fname
    is a flag to specify whether s is a filename, defaulting to False."""
    if fname:
        f = open(s)
        s = f.read()
        f.close()
    inlines = s.splitlines()
    filelen = len(inlines)
    sectionStack = []
    ctrl, line, comments = readComments(inlines)
    if ctrl != "py-section":
        nb = dbutil.createNotebook(session, user, "")
    else:
        nb = dbutil.createNotebook(session, user, line)
    nb.root.comment = '\n'.join(comments)
    sectionStack.append(nb.root)
    active = nb.root
    ctrl, line = control(inlines.pop(0))
    while inlines: # main parsing loop
        if ctrl == 'py-comment': # read comments
            ctrl, line, comments = readComments(inlines, [line])
            if active.comment:
                comments = [active.comment]+comments
            active.comment = '\n'.join(comments)
        elif ctrl == 'py-section': # create a section
            active = models.Section(line)
            sectionStack[-1].addChild(active)
            session.flush()
            sectionStack.append(active)
            ctrl, line = control(inlines.pop(0))
        elif ctrl == 'py-section-end': # close a section
            sectionStack.pop()
            if sectionStack:
                active = sectionStack[-1]
            ctrl, line = control(inlines.pop(0))
        elif ctrl in TEXTS: # read a text block
            end = ctrl
            active = models.TextCell()
            sectionStack[-1].addChild(active)
            session.flush()
            if end in line:
                active.textData = line[:line.find(end)]
                if line[line.find(end)+3:].strip():
                    raise SyntaxError(line)
            else:
                textLines = readText(inlines, end, [line])
                active.textData = '\n'.join(textLines)
            ctrl, line = control(inlines.pop(0))
        elif ctrl is None and line: # read input
            active = models.InputCell()
            sectionStack[-1].addChild(active)
            session.flush()
            ctrl, line, inputs = readInput(inlines, [line])
            active.input = '\n'.join(inputs)
            # if ctrl == "py-output":
        elif ctrl == "py-output":
            if not isinstance(active, models.InputCell):
                raise SyntaxError("%i:%s"%(filelen-len(inlines), line))
            else:
                ctrl, line, outputs = readOutput(inlines, [line])
                active.output += '\n'.join(outputs)
                # active.output += '\n' + line
        else:
            # skip blank lines
            print "skip:",ctrl, line
            ctrl, line = control(inlines.pop(0))
    return nb







