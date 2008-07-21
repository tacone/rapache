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

class AdvancedVhostPlugin:

	def __init__(self, path):
		
		# The path to the plugin
		self.path = path
	
		# module this plugin works with
		self.module = ""
		
		# Define what additional config should be read from vhost file
		self.vhosts_config = { "ServerAdmin" : 0 } # 0 value | 1 options
		
		# Get glade file XML
		f = open( os.path.join(self.path, "vhost.glade") ,"r")
		self.glade_vhost_xml =  f.read()
		f.close()
		
		# Controls
	
	# Customise the module properties window
	def load_module_properties(self, notebook, module):
		return

	# Perform action on module properties save
	def save_module_properties(self, module):
		return
	
	# Customise the vhost properties window
	def load_vhost_properties(self, notebook, vhost_data):
		label = gtk.Label("Advanced")
		
		# Remember you will need to recreate tree everytime the window loads
		wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "table_advanced_vhost")
		table_advanced_vhost = wtree.get_widget("table_advanced_vhost")	
		
		notebook.insert_page(table_advanced_vhost, label)
		
		# make sure to show items
		label.show()
		table_advanced_vhost.show()
		return
		
	# Perform action on vhost properties save
	def save_vhost_properties(self, vhost_data):
		return

def register( path ):
	return AdvancedVhostPlugin( path )

