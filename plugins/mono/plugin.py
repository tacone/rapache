import os
import RapacheGtk.GuiUtils

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

class MonoPlugin:

	def __init__(self, path):
		
		# The path to the plugin
		self.path = path
	
		# module this plugin works with
		self.module = "mod_mono"
		
		# Define what additional config should be read from vhost file
		self.vhosts_config = { "MonoServerPath" : 0 } # 0 value | 1 options
		
		# Get glade file XML
		f = open( os.path.join(self.path, "mono_vhost.glade") ,"r")
		self.glade_vhost_xml =  f.read()
		f.close()
		
		f = open( os.path.join(self.path, "mono_module.glade") ,"r")
		self.glade_module_xml =  f.read()
		f.close()
		
		# Controls
		self.comboboxentry_vhost_mono_version = None
	
	# Customise the module properties window
	def load_module_properties(self, notebook, module):
		label = gtk.Label("Mono Default Config")
		
		# Remember you will need to recreate tree everytime the window loads
		wtree = gtk.glade.xml_new_from_buffer(self.glade_module_xml, len(self.glade_module_xml), "scrolledwindow_mono_config")
		scrolledwindow_mono_config = wtree.get_widget("scrolledwindow_mono_config")	
		textview_mono_config = wtree.get_widget("textview_mono_config")	

		f = open("/etc/mono-server2/mono-server2-hosts.conf", "r")
		config = f.read()
		f.close()
      	        
       	        self.text_view_vhost_source = RapacheGtk.GuiUtils.new_apache_sourceview()
		self.text_view_vhost_source.set_editable( False )
		self.text_view_vhost_source.show()

		buf = self.text_view_vhost_source.get_buffer()
       	        buf.set_text( config )
       	       
       	        
		scrolledwindow_mono_config.remove(textview_mono_config)
		scrolledwindow_mono_config.add(self.text_view_vhost_source)


		# make sure to show items
		notebook.insert_page(scrolledwindow_mono_config, label)
		label.show()
		scrolledwindow_mono_config.show()
		self.text_view_vhost_source.show()
		return

	# Perform action on module properties save
	def save_module_properties(self, module):
	
		return
	
	# Customise the vhost properties window
	def load_vhost_properties(self, notebook, vhost_data):
		label = gtk.Label("Mono (asp.net)")
		
		# Remember you will need to recreate tree everytime the window loads
		wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "vbox_mono_plugin")
		vbox_mono_plugin = wtree.get_widget("vbox_mono_plugin")	

		self.comboboxentry_vhost_mono_version = wtree.get_widget("comboboxentry_vhost_mono_version")
		if not vhost_data["MonoServerPath"]:
			self.comboboxentry_vhost_mono_version.set_active(0)
		elif vhost_data["MonoServerPath"].endswith("mod-mono-server1"):
			self.comboboxentry_vhost_mono_version.set_active(1)
		elif vhost_data["MonoServerPath"].endswith("mod-mono-server2"):
			self.comboboxentry_vhost_mono_version.set_active(2) 
		notebook.insert_page(vbox_mono_plugin, label)
		
		# make sure to show items
		label.show()
		vbox_mono_plugin.show()
		return
		
	# Perform action on vhost properties save
	def save_vhost_properties(self, vhost_data):
		
		selected_option = self.comboboxentry_vhost_mono_version.get_active()
		
		if selected_option == 0:
			vhost_data["MonoServerPath"] = ""
		elif selected_option == 1:
			vhost_data["MonoServerPath"] = "/usr/bin/mod-mono-server1"
		elif selected_option == 2:
			vhost_data["MonoServerPath"] = "/usr/bin/mod-mono-server2"
	
		return

def register( path ):
	return MonoPlugin( path )

