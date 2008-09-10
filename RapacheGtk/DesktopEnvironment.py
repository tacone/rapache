# Rapache - Apache Configuration Tool
# Copyright (C) 2008 Stefano Forenza,  Jason Taylor, Emanuele Gentili
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import os
from RapacheCore import Shell

"""abstracts Desktop Environment's specific operation."""
# TODO: refactor this into a factory to support more than a Desktop Environment easily
#
# care should be taken with userid, we don't want root priviledges when they're not needed


# Grabbed from Ubuntu's UpdateManager (ChangelogViewer.py)    
#  Copyright (c) 2006 Sebastian Heinlein
#                2007 Canonical    
# TODO: move this into an utility module        
def open_url(url):
    """Opens the specified URL in a browser"""
    # Find an appropiate browser
    if os.path.exists('/usr/bin/gnome-open'):
        command = ['gnome-open', url]
    else:
        command = ['x-www-browser', url]
    # Avoid to run the browser as user root
    if os.getuid() == 0 and os.environ.has_key('SUDO_USER'):
        command = ['sudo', '-u', os.environ['SUDO_USER']] + command
    subprocess.Popen(command)

def open_dir( path ):
    # just call this locally as it wont apply over ssh
    command = ['nautilus', path, '--no-desktop']

    if os.access(path, os.W_OK):
        subprocess.Popen( command )
    else:
        subprocess.Popen( ['gksu', subprocess.list2cmdline(command)] )
