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
import gnome.ui

from RapacheGtk import GuiUtils
from RapacheCore import Configuration

class WarningWindow:
	"""The Rapache warning window"""

	def __init__(self, warning, father = None):
		self.father = father
		self.gladefile = Configuration.GLADEPATH + "/" + "warning_dialog.glade"
		print self.gladefile
		self.xml =  gtk.glade.XML(self.gladefile)
		#Create our dictionary and connect it
		dic = { 
			"quit" : gtk.main_quit
			, "on_ok" : gtk.main_quit
			}
		self.xml.signal_autoconnect(dic)
		self.xml.get_widget( 'label1' ).set_label ( warning )  
		                  

