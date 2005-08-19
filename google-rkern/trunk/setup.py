from setuptools import setup, find_packages

setup(name = "notabene",
      version = "0.0",
      packages = find_packages(),
      install_requires = ['lxml>=0.7',
                          'elementtree'],
      
      extras_require = {'reST': ['docutils'],
                       },
      author = "Robert Kern",
      author_email = "rkern@ucsd.edu",
      license = "BSD",
)
