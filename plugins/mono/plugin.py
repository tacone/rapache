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

	def __init__(self):
	
		# module this plugin works with
		# REQUIRED
		self.module = "mod_mono"

	# REQUIRED
	def load_module_properties(self, notebook, module):
		label = gtk.Label("Mono Plugin")
		frame = gtk.Label("Mono Content")
		notebook.insert_page(frame, label, 0)
		label.show()
		frame.show()
		return
	
	def save_module_properties(self, module):
		return
	
	def load_vhost_properties(self, notebook, vhost):
		label = gtk.Label("Mono Plugin")
		frame = gtk.Label("Mono Content")
		notebook.insert_page(frame, label)
		label.show()
		frame.show()
		return
		
	def save_vhost_properties(self, vhost):
		return	GtkFrameObject

def register():
	return MonoPlugin()

