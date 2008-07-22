from Module import ModuleModel

class PluginBaseObject():

	def __init__(self, path):
			
		# The path to the plugin
		self.path = path
	
		# module this plugin works with
		self.module = ""
		
		# Define what additional config should be read from vhost file
		self.vhosts_config = {  } # 0 value | 1 options
	
	def is_module_enabled(self):
		if self.module:
			module = ModuleModel(self.module)
			module.load()
			print "STATUS : " + self.module + " - " + str( module.is_enabled())
			return module.is_enabled()
		return True
		
	def is_enabled(self):
		enabled = self.is_module_enabled()
		
		#TODO: Method of activating / deactivating plugins
		
		return enabled
		
	# Customise the module properties window
	def load_module_properties(self, notebook, module):
		return True

	# Perform action on module properties save
	def save_module_properties(self, module):
		return True

	# Customise the vhost properties window
	def load_vhost_properties(self, notebook, vhost_data):
		return True
		
	# Perform action on vhost properties save
	def save_vhost_properties(self, vhost_data):
		return True
