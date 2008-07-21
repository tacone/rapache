import os
import os.path
import imp
import sys

class PluginManager():

	def __init__(self, pluginpath=None):
	
		print "-- Loading plugins --"
		self.plugins = []

		if pluginpath == None:
			pluginpath = os.path.join(sys.path[0], "plugins")
		print "pluging folder : " + pluginpath
			
		if not pluginpath in sys.path:
			sys.path.insert(0, pluginpath)

		for folder in os.listdir(pluginpath):
			if os.path.isdir(os.path.join(pluginpath,folder)):				
				try:
					module = __import__(folder + ".plugin")
					obj = module.plugin.register()
					self.plugins.append(obj)
					print "loaded plugin : " + folder
				except:
					print "error loading plugin " + folder
		
		print ""
		print ""
