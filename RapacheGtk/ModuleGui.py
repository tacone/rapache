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
        
        signals = {
            "on_button_save_clicked"            : self.on_button_save_clicked,
            "on_button_cancel_clicked"          : self.on_button_cancel_clicked,
            "on_module_doc_button_clicked"      : self.on_module_doc_button_clicked
        }
        wtree.signal_autoconnect(signals)            
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)
        
        self.text_view_module_conf = GuiUtils.new_apache_sourceview()        
        self.text_view_module_conf.show()
        wtree.get_widget("text_view_module_conf_area").add(self.text_view_module_conf)
        
        GuiUtils.change_button_label( self.module_doc_button, 'Documentation' )
        GuiUtils.style_as_tooltip( self.error_area )
    def run(self):
        self.window.show()           
        gtk.main()

    def load (self, name ):
        self.window.set_title(name)
        self.module = ModuleModel ( name )
        #self.module.load()
        buf = self.text_view_module_conf.get_buffer()
        buf.set_text( self.module.get_configuration() )
        
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
