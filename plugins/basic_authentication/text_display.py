#!/usr/bin/env python

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

import sys
try:
     import pygtk
     pygtk.require("2.0")
except:
      pass
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)

import os

class UserCredentials:
    
    def __init__(self, path):

        # The path to the plugin
        self.glade_path = path
                  
        gladefile = os.path.join(path, "basic_auth.glade")
        wtree = gtk.glade.XML(gladefile)
        
        self.window = wtree.get_widget("dialog_edit_user")
        
        self.entry_username = wtree.get_widget("entry_username")
        self.entry_password = wtree.get_widget("entry_password")
        self.entry_password = wtree.get_widget("entry_password")

        signals = {
           "on_button_apply_clicked"        : self.on_button_apply_clicked,
           "on_button_close_clicked"        : self.on_button_close_clicked
        }
        wtree.signal_autoconnect(signals)            
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)

        self.return_value = None
        
    def on_button_apply_clicked(self, widget):
        self.return_value = gtk.RESPONSE_OK
        self.window.destroy()
        return
        
    def on_button_close_clicked(self, widget):
        self.window.destroy()
        return

    def run(self):
        self.window.show()   
        gtk.main()
        return self.return_value
   
    def load (self, username):
        self.entry_username.set_text( username) 
        return
				
    def on_destroy(self, widget, data=None):
        gtk.main_quit()

