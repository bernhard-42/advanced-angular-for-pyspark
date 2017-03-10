import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "zeppelin_session",
    version = "0.9.3",
    author = "Bernhard Walter",
    author_email = "bwalter@gmail.com",
    description = ("Extending Apache Zeppelin Angular display system with functions "
                   "to register, unregister and call javascript functions"),
    license = "Apache License 2.0",
    keywords = "zeppelin angular javascript",
    packages=['zeppelin_session'],
    long_description=read('Readme.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "Programming Language :: Python'",
        "Programming Language :: Python :: 2'",
        "Programming Language :: Python :: 3'"
    ]
)