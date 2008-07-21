import os
import gtksourceview

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
		
		buf = textview_mono_config.get_buffer()
       	        buf.set_text( config )

		bufferS = gtksourceview.SourceBuffer()
		manager = gtksourceview.SourceLanguagesManager()
		language = manager.get_language_from_mime_type("text/xml")
		#langS.set_mime_types(["text/x-python"])
		bufferS.set_language(language)
		bufferS.set_highlight(True)
		view = gtksourceview.SourceView(bufferS)
		view.set_show_line_numbers(True)

		buf = view.get_buffer()
       	        buf.set_text( config )
       	        view.show()

		# make sure to show items
		notebook.insert_page(view, label)
		label.show()
		scrolledwindow_mono_config.show()
		return

	# Perform action on module properties save
	def save_module_properties(self, module):
	
		return
	
	# Customise the vhost properties window
	def load_vhost_properties(self, notebook, vhost):
		label = gtk.Label("Mono (asp.net)")
		
		# Remember you will need to recreate tree everytime the window loads
		wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "vbox_mono_plugin")
		vbox_mono_plugin = wtree.get_widget("vbox_mono_plugin")	

		self.comboboxentry_vhost_mono_version = wtree.get_widget("comboboxentry_vhost_mono_version")
		self.comboboxentry_vhost_mono_version.set_active(0)

		notebook.insert_page(vbox_mono_plugin, label)
		
		# make sure to show items
		label.show()
		vbox_mono_plugin.show()
		return
		
	# Perform action on vhost properties save
	def save_vhost_properties(self, vhost):
		return

def register( path ):
	return MonoPlugin( path )

