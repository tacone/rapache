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

""".
Issues with the new window:
    - self.parent doesn't work
    - onblur doesn't trigger when pressing Return
    - changing a domain name doesn't change subdomains
    - empty server aliases shuoldn't be managed
ALSO:
    - please implement a delete directive func in the parser
    - move denorm. vhosts in another tab
    - merge with Qense warning window
"""

import sys
import re

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
import pango
import tempfile
import traceback
import RapacheGtk.GuiUtils
from RapacheCore.Module import *
from RapacheGtk import GuiUtils
import RapacheGtk.DesktopEnvironment as Desktop
import RapacheCore.Shell

def open_module_doc( name ):
        if ( name == None ): return False
        url = "http://httpd.apache.org/docs/2.2/mod/mod_%s.html" % name
        Desktop.open_url( url )
        
class ModuleWindow:
    
    def __init__ ( self, parent = None):
           
        self.module = None
        self.create_new = True
        self.parent = parent
        
        gladefile = os.path.join(Configuration.GLADEPATH, "edit_module.glade")
        wtree = gtk.glade.XML(gladefile)
        
        self.window = wtree.get_widget("dialog_edit_module")
        #self.text_view_module_conf = wtree.get_widget("text_view_module_conf")
        self.notebook = wtree.get_widget("notebook")
        self.button_save = wtree.get_widget("button_save")
        self.error_area = wtree.get_widget("error_area")
        self.module_doc_button = wtree.get_widget("module_doc_button")
        self.label_module = wtree.get_widget("label_module")
        self.label_module_description = wtree.get_widget("label_module_description")
        self.combobox_module_backups = wtree.get_widget("combobox_module_backups")
        self.label_path = wtree.get_widget("label_path")
        self.combobox_module_backups.set_active(0)

        signals = {
            "on_button_save_clicked"            : self.on_button_save_clicked,
            "on_button_cancel_clicked"          : self.on_button_cancel_clicked,
            "on_module_doc_button_clicked"      : self.on_module_doc_button_clicked,
            "on_combobox_module_backups_changed" : self.on_combobox_module_backups_changed,
            "on_button_restore_version_clicked" : self.on_button_restore_version_clicked
        }
        wtree.signal_autoconnect(signals)            
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)
        
        self.text_view_module_conf = GuiUtils.new_apache_sourceview()        
        self.text_view_module_conf.show()
        wtree.get_widget("text_view_module_conf_area").add(self.text_view_module_conf)
        
        #GuiUtils.change_button_label( self.module_doc_button, 'Documentation' )
        GuiUtils.style_as_tooltip( self.error_area )

    def run(self):
        self.window.show()           
        gtk.main()

    def on_combobox_module_backups_changed(self, widget):
        return

    def on_button_restore_version_clicked(self, widget):
        
        if self.text_view_module_conf.get_buffer().get_modified():
            md = gtk.MessageDialog(self.window, flags=0, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL, message_format="Are you sure, you will lose all your current changes")
            result = md.run()
            md.destroy()
            if result != gtk.RESPONSE_OK:
                return
        
        selected = self.combobox_module_backups.get_active()
        
        if selected == 0:
            self.__set_module_conf( self.module.get_configuration() )
        else:
            value = self.combobox_module_backups.get_active_text()[7:]
            self.__set_module_conf( self.module.get_configuration_version(value) )
       
    def __set_module_conf(self, text):
        buf = self.text_view_module_conf.get_buffer()
        buf.set_text( text )
        buf.set_modified(False)
        

    def load (self, name ):
       # self.window.set_title(name)
        self.module = ModuleModel ( name )
        #self.module.load()
        self.__set_module_conf( self.module.get_configuration() )
        
        self.label_module.set_markup("<b><big>Apache2 Module : " + name + "</big></b>")
        self.label_module_description.set_markup("<i>" + self.module.get_description() + "</i>")
        self.label_path.set_text( "File : " + self.module.get_configuration_file_name() )
        for file in self.module.get_backup_files():
            self.combobox_module_backups.append_text("Backup " + file[0][-21:-4])

         # Load UI Plugins
        for plugin in self.parent.plugin_manager.plugins:
        	if plugin.module == name:
			try:
				print "Loading plugin " + name
				plugin.load_module_properties(self.notebook, self.module)
			except Exception:
				traceback.print_exc(file=sys.stdout)
				

    def on_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_button_save_clicked(self, widget):
        
        name = self.module.data['name']
        print "Current name:", name
        buff = self.text_view_module_conf.get_buffer()
        text = buff.get_text(buff.get_start_iter(), buff.get_end_iter())

        mod = ModuleModel( name )
        mod.save_configuration( text )
        
        #self.parent.refresh_vhosts()
        self.parent.please_restart()
        self.window.destroy()
                               
    def on_button_cancel_clicked(self, widget):
        self.window.destroy()
        return    
    def on_module_doc_button_clicked (self, widget ):
        name = self.module.data['name']
        open_module_doc(name)
    def show_error ( self, message ):
        
        self.xml.get_widget( 'message_text' ).set_label( '<b>'+message+'</b>' )
        self.xml.get_widget( 'message_container' ).show()
