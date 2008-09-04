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

# https://help.ubuntu.com/community/ModMono

import os

from RapacheCore import Shell
import RapacheGtk.GuiUtils
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

class MonoPlugin(PluginBaseObject):

    def __init__(self, path):
        
        # The path to the plugin
        self.path = path
    
        # module this plugin works with
        self.module = "NONE"
        
        # config
        self.mono1_1_path = "/usr/bin/mod-mono-server"
        self.mono2_0_path = "/usr/bin/mod-mono-server2"

        self.is_mono1_1 = Shell.command.exists(self.mono1_1_path)
        self.is_mono2_0 = Shell.command.exists(self.mono2_0_path)

        # Controls
        self.comboboxentry_vhost_mono_version = None

    def init_vhost_properties(self):
    
        # Get glade file XML
        f = open( os.path.join(self.path, "mono_vhost.glade") ,"r")
        self.glade_vhost_xml =  f.read()
        f.close()
        
        # Remember you will need to recreate tree everytime the window loads
        wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "vbox_mono_plugin")
        vbox_mono_plugin = wtree.get_widget("vbox_mono_plugin")    

        self.comboboxentry_vhost_mono_version = wtree.get_widget("comboboxentry_vhost_mono_version")

        # remove version if not present in system
        if not self.is_mono2_0:
            self.comboboxentry_vhost_mono_version.remove_text(2)
        if not self.is_mono1_1:
            self.comboboxentry_vhost_mono_version.remove_text(1)
  
  
  
        icon_theme = gtk.icon_theme_get_default()
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(self.path, "mono.jpeg"), 24, 24)
        #pixbuf = icon_theme.lookup_icon("monodoc", 24, 0).load_icon()

        return vbox_mono_plugin, "Mono", pixbuf

    
    # Customise the vhost properties window
    def load_vhost_properties(self, vhost):
        
        if not vhost.config.MonoServerPath:
            self.comboboxentry_vhost_mono_version.set_active(0)
        elif self.is_mono1_1 and vhost.config.MonoServerPath.value == self.mono1_1_path:
            self.comboboxentry_vhost_mono_version.set_active(1)
        elif self.is_mono2_0 and vhost.config.MonoServerPath.value == self.mono2_0_path:
            self.comboboxentry_vhost_mono_version.set_active(2) 

        return
        
    # Perform action on vhost properties save
    def update_vhost_properties(self, vhost):
        """
        selected = self.comboboxentry_vhost_mono_version.get_active_text()
        
        if selected.count("1.1") > 0:
            vhost.config.MonoServerPath.value = self.mono1_1_path
        elif selected.count("2.0") > 0:
            vhost.config.MonoServerPath.value = self.mono2_0_path
        elif vhost.config.MonoServerPath:
            del vhost.config.MonoServerPath
 
 
        ds = vhost.config.Directory.search(  [vhost.get_document_root()]  )
        d = None
        if len(ds) == 0:
            d = vhost.config.sections.create("Directory", vhost.get_document_root())
        else:
            d = ds[0]
            
            if vhost.config.MonoServerPath:
                d.SetHandler.value = "mono"
                d.AddHandler.opts = ["mod_mono", ".aspx", ".ascx", ".asax",".ashx",".config",".cs",".asmx"]
            elif d.SetHandler:
                del d.SetHandler

        """
        return True, None
        
    # Perform action on vhost properties save
    def save_vhost_properties(self, vhost):

        #Shell.command.write_file( self.entry_location.get_text(), self.users.save())
        
        return True, None
        
def register( path ):
    return MonoPlugin( path )

