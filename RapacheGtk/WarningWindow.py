#!/usr/bin/env python

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
		                  

