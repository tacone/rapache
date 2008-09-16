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
		self.__add("/usr/lib/rapache/plugins")
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
		
		
