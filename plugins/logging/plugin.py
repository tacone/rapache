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
from RapacheCore.PluginBase import PluginBaseObject
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



class AdvancedVhostPlugin(PluginBaseObject):

    def __init__(self, path):
        
        # The path to the plugin
        self.path = path
    
        # module this plugin works with
        self.module = ""
        
        # Define what additional config should be read from vhost file
        self.vhosts_config = { "ServerAdmin" : 0, "LogLevel" : 0, "ErrorLog" : 0, "ServerSignature" : 0 } # 0 value | 1 options
        
        # Controls
        self.entry_admin_email = None
        self.entry_log_location = None
        self.combobox_log_level = None
        self.checkbutton_server_signature = None
        
        self.log_levels = ["emerg", "alert", "crit", "error", "warn", "notice", "info", "debug"]    
    
    
    def init_vhost_properties(self):

        # Get glade file XML
        f = open( os.path.join(self.path, "logging.glade") ,"r")
        self.glade_vhost_xml =  f.read()
        f.close()
    
        # Remember you will need to recreate tree everytime the window loads
        wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "table_advanced_vhost")
        table_advanced_vhost = wtree.get_widget("table_advanced_vhost")    
        self.entry_admin_email =  wtree.get_widget("entry_admin_email")    
        self.entry_log_location = wtree.get_widget("entry_log_location")    
        self.combobox_log_level = wtree.get_widget("combobox_log_level")
        self.checkbutton_server_signature = wtree.get_widget("checkbutton_server_signature")

        return table_advanced_vhost, gtk.Label("Logging")
        
    # Customise the vhost properties window
    def load_vhost_properties(self, vhost):
                
        self.entry_admin_email.set_text(vhost.get_value("ServerAdmin", ""))
        self.entry_log_location.set_text(vhost.get_value("ErrorLog", ""))
        if vhost.get_value("LogLevel"):
            self.combobox_log_level.set_active( self.log_levels.index( vhost.get_value("LogLevel") ) )
        if vhost.get_value("ServerSignature", "off").lower() != "off":
            self.checkbutton_server_signature.set_active(True)

        return
        
    # Perform action on vhost properties save
    def save_vhost_properties(self, vhost):
    
        vhost.set_value("ServerAdmin", self.entry_admin_email.get_text())
        vhost.set_value("ErrorLog", self.entry_log_location.get_text())
        vhost.set_value("LogLevel", self.log_levels[ self.combobox_log_level.get_active() ] )
        if self.checkbutton_server_signature.get_active():
             vhost.set_value("ServerSignature", "on" )
        else:
             vhost.set_value("ServerSignature", "off")
        
        
        server_admin = self.entry_admin_email.get_text()
                    
        return True, None

def register( path ):
    return AdvancedVhostPlugin( path )

