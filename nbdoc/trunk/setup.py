from distutils.core import setup

setup(name = "nbdoc",
      version = "0.1",
      packages = ['notabene', 'notabene.testing', 'notabene.normalization'],
      package_data = {'notabene': ['xsl/VERSION',
                                   'xsl/README*',
                                   'xsl/*/*.*',
                                   'xsl/*/*/*.*',
                                   'xsl/*/*/*/*.*',
                                   ]},
      description = "ipython notebook document generation",
      long_description = 
"""notabene is the document generation component for the ipython notebook
project.
""",
      author = "Robert Kern",
      author_email = "rkern@enthought.com",
      maintainer = "Toni Alatalo",
      maintainer_email = "antont@an.org",
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

