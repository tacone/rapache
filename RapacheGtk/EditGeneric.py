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
import RapacheGtk.GuiUtils
from RapacheCore.Module import *
from RapacheGtk import GuiUtils
import RapacheCore.Shell

class EditGenericWindow:
    
    def __init__(self):
                     
        gladefile = os.path.join(Configuration.GLADEPATH, "edit_generic.glade")
        wtree = gtk.glade.XML(gladefile)
        
        self.window = wtree.get_widget("dialog_edit_generic")
        
        self.scrolledwindow_generic = wtree.get_widget("scrolledwindow_generic")
        self.label_path = wtree.get_widget("label_path")
        self.combobox_backups = wtree.get_widget("combobox_backups")
        
        signals = {
           "on_button_save_clicked"         : self.on_button_save_clicked,
           "on_button_cancel_clicked"        : self.on_button_cancel_clicked,
           "on_button_restore_version_clicked" : self.on_button_restore_version_clicked
        }
        wtree.signal_autoconnect(signals)            
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)

        self.text_view_source = GuiUtils.new_apache_sourceview()
        self.scrolledwindow_generic.add( self.text_view_source )
        self.text_view_source.show()

        self.return_value = None

    def on_button_restore_version_clicked(self, widget):
        buf = self.text_view_source.get_buffer()
        buf.set_text( Shell.command.read_file( self.file_path ) )

        if self.text_view_source.get_buffer().get_modified():
            md = gtk.MessageDialog(self.window, flags=0, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL, message_format="Are you sure, you will lose all your current changes")
            result = md.run()
            md.destroy()
            if result != gtk.RESPONSE_OK:
                return
        
        selected = self.combobox_backups.get_active()
        
        if selected == 0:
            buf.set_text( Shell.command.read_file( self.file_path ) )
        else:
            value = self.combobox_backups.get_active_text()[7:]
            buf.set_text( Shell.command.read_file_version( self.file_path, value ) )
       
        buf.set_modified(False) 

    def on_button_cancel_clicked(self, widget):
        self.window.destroy()
        return

    def on_button_save_clicked(self, widget):
       
        buff = self.text_view_source.get_buffer()
        text = buff.get_text(buff.get_start_iter(), buff.get_end_iter())

        Shell.command.write_file(self.file_path, text)
        
        self.window.destroy()
        return

    def run(self):
        self.window.show()   
        gtk.main()
        return self.return_value
   
    def load (self, path):
    
        self.file_path = path
    
        self.window.set_title("Edit " + path)
        self.label_path.set_text( path )
        
        for file in Shell.command.get_backup_files( path ):
            self.combobox_backups.append_text("Backup " + file[0][-21:-4])
        self.combobox_backups.set_active(0)
        
        buf = self.text_view_source.get_buffer()
        buf.set_text( Shell.command.read_file( path ) )
        buf.set_modified(False) 
        
        return
				
    def on_destroy(self, widget, data=None):
        gtk.main_quit()

