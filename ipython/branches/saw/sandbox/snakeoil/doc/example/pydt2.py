#-# ============================
#-#  Another py2doctest example
#-# ============================

#-# This simple example uses non-default text marks, using '#-# ' to mark text
#-# instead of '### '.  You can still generate the proper output by using::
#-#
#-#   py2doctest.py -t "#-# " -s pydt2.py
#-#

#-# If you want to leave blank lines of input text, the parser allows any
#-# trailing whitespace to be ommitted from the text mark, as above.  You can
#-# also leave the line blank, without any text marks:

#-# will give you a blank line above.  Pure blank lines are needed in cases such
#-# as above, where verbatim input preceeded Python code (reST parsers require a
#-# blank lines enclosing verbatim input).

#-# Some regular Python code, defining a class.  Remember no blank lines inside!
class Foo(object):
    pass

f = Foo()
f.x = 1
print f.x
