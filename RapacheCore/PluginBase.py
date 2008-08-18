from Module import ModuleModel

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

class PluginBaseObject():

    def __init__(self, path):
            
        # The path to the plugin
        self.path = path
    
        # module this plugin works with
        self.module = ""
        
        # Define what additional config should be read from vhost file
        self.vhosts_config = {  } # 0 value | 1 options
        
        # Number set when plugin UI is added to notebook
        self._tab_number = -1
    
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
        
    # Add item to tools menu
    def init_main_window(self, MainWindow):
        return None
        
        
    # Customise the module properties window
    def load_module_properties(self, notebook, module):
        return True

    # Perform action on module properties save
    def save_module_properties(self, module):
        return True






    # Init the vhost propertis window
    def init_vhost_properties(self, notebook):
        return True

    # Tab recives focus load properties from vhost object
    def load_vhost_properties(self,  vhost):
        return True
        
    # Tab blurs update vhost object with changes
    def update_vhost_properties(self, vhost):
        return True
        
    # Perform action on vhost properties save, return false if validation fails
    def save_vhost_properties(self, vhost):
        return True
