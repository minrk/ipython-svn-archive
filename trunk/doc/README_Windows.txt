Notes for Windows Users
=======================

Requirements
------------

IPython runs under (as far as the Windows family is concerned):

- Windows XP (I think WinNT/2000 are ok): works, except for terminal coloring.

- Windows 95/98/ME: I have no idea. It should work, but I can't test.

- CygWin environments may work, I just don't know.

It needs Python 2.1 or newer.

For the automatic installer to work you need Mark Hammond's PythonWin
extensions (and they're great for anything Windows-related anyway, so you
might as well get them). If you don't have them, get them at:

http://starship.python.net/crew/mhammond/

If you won't/can't get them, you'll have to make some shortcuts by hand, but
IPython itself will still work. It's only the install routine that uses the
PythonWin extensions.


Installation
------------

Double-click the setup.py file. A text console should open and proceed to
install IPython in your system. If all goes well, that's all you need to do.
You should now have an IPython entry in your Start Menu.

If you don't have PythonWin, you can:

  - Copy the doc/ directory wherever you want it (it contains the manuals in
HTML and PDF).
  - Create a shortcut to the main IPython script, located in the Scripts
subdirectory of your Python installation directory.

These steps are basically what the auto-installer does for you.
