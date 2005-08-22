import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name = "nbshell",
    version = "0.1",
    #packages = ['nbshell']
    packages = find_packages()
)
