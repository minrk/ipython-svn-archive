# encoding: utf-8
# -*- test-case-name: ipython1.test.test_notebook_xmlutil -*-
"""The Sparse Representation of Notebook components
Sparse Notebooks are simple representations of notebooks.  Tags are not
supported, nor is TextCell Formatting.  Sparse Notebooks are valid
executable Python.  Inputs are unprefixed, and without decoration.  Outputs
are prefixed with '#>'.  Arbitrary layers of Sections can be used for
organizational purposes when loading the notebook into an interactive
environment.  Sections can be opened with control lines, such as:
`# py-section the rest of the line is the title`
Sections can be closed with: `# py-section-end`
note: whitespace is trimmed, so any `^\s*#\s*py-section\s*Title Stuff\s*$` is
valid.
Comments are attached to objects, and they go after the object to which they
are attached.
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
CONTROLS = ["py-section", "py-section-end"]
    
# def __init__(self, user):
#     self.user = user
#     # self.session = session
#     self.sectionStack = []

def control(line):
    if line[:2] == OUTPUT:
        return "py-output", line[2:]
    elif line[:3] in TEXTS:
        return line[:3], line[3:]
    elif line and line.strip()[0] == '#':
        line = line.strip()[1:]
        splits = map(str.strip, line.strip().split(' ',1))
        if len(splits) > 0:
            if splits[0] in CONTROLS:
                if len(splits) > 1:
                    return splits[0], splits[1]
                else:
                    return splits[0] , ""
        return 'py-comment', line
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
    # print "cmt:",comments
    return ctrl, line, comments

def readInput(inlines, inputs=[]):
    ctrl, line = control(inlines.pop(0))
    while inlines and ctrl is None:
        inputs.append(line)
        ctrl, line = control(inlines.pop(0))
    # print "inp:",inputs
    return ctrl, line, inputs

def readOutput(inlines, outputs=[]):
    ctrl, line = control(inlines.pop(0))
    while inlines and ctrl == "py-output":
        outputs.append(line)
        ctrl, line = control(inlines.pop(0))
    # print "out:",outputs
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
            if not isinstance(active, models.InputCell) or active.output != "":
                # create new input if active is not IO, or if we have
                # already written to the output
                active = models.InputCell()
                sectionStack[-1].addChild(active)
                session.flush()
            ctrl, line, inputs = readInput(inlines, [line])
            if active.input: #append, so we are missing a '\n'
                active.input += '\n'
            active.input += '\n'.join(inputs)
        elif ctrl == "py-output":
            if not isinstance(active, models.InputCell):
                raise SyntaxError("%i:%s"%(filelen-len(inlines), line))
            else:
                ctrl, line, outputs = readOutput(inlines, [line])
                if active.output: #append, so we are missing a '\n'
                    active.output += '\n'
                active.output += '\n'.join(outputs)
                # active.output += '\n' + line
        else:
            # skip blank lines
            # print "skip:",ctrl, line
            ctrl, line = control(inlines.pop(0))
    return nb







