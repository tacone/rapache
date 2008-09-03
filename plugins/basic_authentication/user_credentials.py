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
        self.entry_password2 = wtree.get_widget("entry_password2")

        signals = {
           "on_button_apply_clicked"        : self.on_button_apply_clicked,
           "on_button_close_clicked"        : self.on_button_close_clicked
        }
        wtree.signal_autoconnect(signals)            
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)

        self.return_value = None
        
    def on_button_apply_clicked(self, widget):
        error_text = None
        # check password etc
        if len(self.entry_username.get_text().strip()) < 1:
            error_text = "Sorry your username must be at least 1 character"
        
        elif self.entry_password.get_text() != self.entry_password2.get_text():
            error_text = "Sorry your passwords do not match"
        
        elif len(self.entry_password.get_text()) < 4:
            error_text = "Sorry your password should be at least 4 characters"

        if error_text:
            md = gtk.MessageDialog(self.window, flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=error_text) 
            md.run()
            md.destroy()
            return

        self.return_value = self.entry_username.get_text().strip(), self.entry_password.get_text()
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
        self.entry_username.set_sensitive(False)
        return
				
    def on_destroy(self, widget, data=None):
        gtk.main_quit()

