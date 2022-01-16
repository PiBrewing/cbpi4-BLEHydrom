from setuptools import setup
import os
from setuptools.command.install import install
from subprocess import check_call


class PreInstallCommand(install):
    """Pre-installation for installation mode."""
    def run(self):
        check_call("apt-get install pkg-config libboost-python-dev libboost-thread-dev libbluetooth-dev libglib2.0-dev python3-dev".split())
        install.run(self)

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(name='cbpi4-BLEHydrom',
      version='0.0.3',
      description='CraftBeerPi4 Plugin for Hydrom and Tilt (BLE connection)',
      author='Alexander Vollkopf',
      author_email='avollkopf@web.de',
      url='',
      include_package_data=True,
      package_data={
        # If any package contains *.txt or *.rst files, include them:
      '': ['*.txt', '*.rst', '*.yaml'],
      'cbpi4-BLEHydrom': ['*','*.txt', '*.rst', '*.yaml']},
      packages=['cbpi4-BLEHydrom'],
      install_requires=[
      'PyBluez==0.23',
      'gattlib==0.20201113',
      ],
      long_description=long_description,
      long_description_content_type='text/markdown'
     )
