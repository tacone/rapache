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
    """Open the specified URL in a browser"""
    # Find an appropiate browser
    if os.path.exists('/usr/bin/gnome-open'):
        command = ['gnome-open', url]
    else:
        command = ['x-www-browser', url]
    # Avoid to run the browser as user root
    if os.getuid() == 0 and os.environ.has_key('SUDO_USER'):
        command = ['sudo', '-u', os.environ['SUDO_USER']] + command
    subprocess.Popen(command)
def open_dir( path):
    Shell.command ('gksudo "nautilus '+path+' --no-desktop" & ' )
