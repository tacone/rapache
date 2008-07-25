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
import re
import os

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

from RapacheCore.VirtualHost import *
from RapacheGtk import GuiUtils
        
class EditDomainNameWindow:

	def __init__ ( self, domain = ""):
		self.return_value = None
		
		gladefile = os.path.join(Configuration.GLADEPATH, "edit_domain_name.glade")
		wtree = gtk.glade.XML(gladefile)
		
		self.window = wtree.get_widget("dialog_edit_domain_name")
        	self.entry_domain = wtree.get_widget("entry_domain")
        	self.label_heading = wtree.get_widget("label_heading")
        	self.image_icon = wtree.get_widget("image_icon")

        	signals = {
			"on_button_ok_clicked"        	: self.on_button_ok_clicked,
			"on_button_cancel_clicked"      : self.on_button_cancel_clicked
		}
		wtree.signal_autoconnect(signals)
		
		# add on destroy to quit loop
		self.window.connect("destroy", self.on_destroy)
		
		if domain:
			self.entry_domain.set_text( domain )
        
        def run(self):
        	self.window.show()
        	self.entry_domain.select_region(0,-1)
        	gtk.main()
         	
        	return self.return_value

        def on_destroy(self, widget, data=None):
		gtk.main_quit()

	def on_button_ok_clicked(self, widget):
		self.return_value = self.entry_domain.get_text()
		self.window.destroy()
        	return         	
        	
	def on_button_cancel_clicked(self, widget):
		self.window.destroy()
        	return    
        	    	
