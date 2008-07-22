import os
import os.path
import imp
import sys
import traceback
class PluginManager():

	def __init__(self):
	
		print "-- Loading plugins --"
		self.plugins = []
		self.__add(os.path.join(sys.path[0], "plugins"))
		self.__add(os.path.expanduser("~/.rapache/plugins"))
		print ""
		
	def __add(self, pluginpath):

		print "checking plugin folder : " + pluginpath
			
		if not pluginpath in sys.path:
			sys.path.insert(0, pluginpath)

		if os.path.exists(pluginpath):
			for folder in os.listdir(pluginpath):
				path = os.path.join(pluginpath,folder)
				if os.path.isdir(path):				
					try:
						module = __import__(folder + ".plugin")
						obj = module.plugin.register(path)
						self.plugins.append(obj)
						print "loaded plugin : " + folder
					except:
						print "error loading plugin " + folder
						traceback.print_exc(file=sys.stdout)
		
		
