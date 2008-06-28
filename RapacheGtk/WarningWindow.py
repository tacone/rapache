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

from RapacheGtk import GuiUtils

class WarningWindow:
	"""The Rapache warning window"""

	def __init__(self, warning, father = None):
		self.father = father
		self.gladefile = Configuration.GLADEPATH + "/" + "warning_dialog.glade"  
		#Create our dictionary and connect it
		dic = { 
			"quit" : self.close
			, "on_ok" : self.close
			}
		self.xml.signal_autoconnect(dic)
		self.xml.get_widget( 'label1' ).set_label ( warning )  
		                  
	def close ( self, widget = None ):
		self.window = self.xml.get_widget( 'warning_dialog' )
		self.window.destroy()
