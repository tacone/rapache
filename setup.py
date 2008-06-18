#!/usr/bin/python

import subprocess, glob, os.path
from os import path
from distutils.core import setup
setup(
    name='rapache',
    author='Rapache Developers',
    author_email='rapache-devel@lists.launchpad.net',
    maintainer='Emanuele Gentili',
    maintainer_email='emgent@ubuntu.com',
    description='Simple tool for managing and configuring an apache2 instance',
    url = 'http://www.rapache.org',
    license='GNU GPL',
    packages=['RapacheCore', 'RapacheGtk'],
    scripts=['rapache', 'hosts-manager'],
    data_files=[
                ('share/rapache/Glade', glob.glob('Glade/*')),
                ('share/applications', ['data/rapache.desktop']),
               ],
    )

