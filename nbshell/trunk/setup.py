from distutils.core import setup

setup(
    name = "nbshell",
    author = "Tzanko Matev",
    author_email = "tsanko@gmail.com",
    version = "0.1",
    packages = ['nbshell', 'nbshell.plotting_backends'],
    classifiers = [f.strip() for f in """
        Development Status :: 3 - Alpha
        Intended Audience :: Developers
        Intended Audience :: Science/Research
        License :: OSI Approved :: BSD License
        Operating System :: MacOS :: MacOS X
        Operating System :: Microsoft :: Windows
        Operating System :: POSIX
        Programming Language :: Python
        Topic :: Scientific/Engineering
        Topic :: Software Development :: Documentation
        Topic :: Software Development :: Libraries :: Python Modules
        Topic :: Text Processing :: Markup :: XML
        Topic :: Text Processing :: Markup :: HTML
        Topic :: Text Processing :: Markup :: LaTeX
        """.splitlines() if f.strip()],
)
