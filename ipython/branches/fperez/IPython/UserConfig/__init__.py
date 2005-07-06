"""Dummy file so that distutils installs everything in this directory.

This directory isnt' really a package, though. Some of the files here aren't
even real pyhton files, I'm just using the naming convention to fool
distutils.

Another butt ugly hack here: the ipythonrc files aren't really python files,
but we need to mark them as .py files so they get copied by distutils. The
problem is it will generate error messages when it tries to byte-compile
them. Oh well... From what I've seen so far, distutils is still pretty crude
and clumsy, so we make do with what we have.  """

__all__ = []
