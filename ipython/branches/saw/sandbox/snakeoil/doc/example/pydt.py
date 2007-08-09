### ====================
###  py2doctest example
### ====================

### This is a small example illustrating the use of py2doctest.  py2doctest is
### a simple facility to turn any Python script into valid doctest, with
### interspersed textual input.  The result is valid reST, so you can use reST
### constructs in your input.

### All lines that start with '### ' (note the space) are considered to be
### textual input, and are fed to the output after stripping them of that
### initial marker (including the initial space).  They can thus contain
### arbitrary reST.  Any other line is fed to a real interactive Python
### instance.  For example:

for i in range(10):
    print i,

### Note that since this input is actually passed to a real running interactive
### Python (via pexpect), you must adhere to a few restrictions.  In
### particular, you must leave a blank line after the end of a sequence of
### *indented* statements and before starting either a text block or new input,
### such as the case above.  This is because the interactive session uses a
### single blank line as the indicator that you're done entering input and it
### can run the whole accumulated block.

### For the same reason, you *can not* leave blank lines inside multiline
### blocks, such as function or class definitions.  That would cause the
### interpreter to stop parsing the input at that point!  So a function must be
### defined as follows, without *any* blank lines in it:

def f(x):
    """Return x^2"""
    # Note that the following line is NOT blank, it has 4 spaces in it.
    # If you leave it purely empty, you'll get an error:
    
    return x**2

### Normal input statements.  Note that you don't need blank lines before
### starting normal input (py2doctest adds it for you so the result is valid
### reST for compilation to HTML or other formats):
x = 1
y = 2
print f(x)+f(y)
print f(x+y)
### And it's OK to put text here, also without any preceding blank lines.

print 'x+y=',x+y
