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
from EditDocumentNameGui import EditDocumentNameWindow
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

    def update_tree(self):
        store = gtk.ListStore(str, str)
        self.treeview_default_document.set_model(store)
        for doc in self.documents:
            store.append((doc,doc))


    def init_vhost_properties(self):

        # Get glade file XML
        f = open( os.path.join(self.path, "logging.glade") ,"r")
        self.glade_vhost_xml =  f.read()
        f.close()
    
        # Remember you will need to recreate tree everytime the window loads
        wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "vbox_advanced_host")
        vbox_advanced_host= wtree.get_widget("vbox_advanced_host")    
        self.entry_admin_email =  wtree.get_widget("entry_admin_email")    
        self.entry_log_location = wtree.get_widget("entry_log_location")    
        self.combobox_log_level = wtree.get_widget("combobox_log_level")
        self.checkbutton_server_signature = wtree.get_widget("checkbutton_server_signature")
        self.treeview_default_document = wtree.get_widget("treeview_default_document")

        
        signals = {
           "on_toolbutton_document_add_clicked" : self.on_toolbutton_document_add_clicked,
           "on_toolbutton_document_edit_clicked" : self.on_toolbutton_document_edit_clicked,
           "on_toolbutton_document_delete_clicked" : self.on_toolbutton_document_delete_clicked
        }
        wtree.signal_autoconnect(signals) 
        
        # Setup tree
        column = gtk.TreeViewColumn(('Documents'))
        column.set_spacing(4)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=0)
        self.treeview_default_document.append_column(column)

        icon_theme = gtk.icon_theme_get_default()
        pixbuf = icon_theme.load_icon(gtk.STOCK_PROPERTIES, 24, 0)
 
        return vbox_advanced_host, "Advanced", pixbuf


    def on_toolbutton_document_add_clicked(self, widget):
        edw = EditDocumentNameWindow(self.path, None)
        document = edw.run()
        if document:
            self.treeview_default_document.get_model().append((document, None))
        return
        return
    def on_toolbutton_document_edit_clicked(self, widget):
        
        model, iter = self.treeview_default_document.get_selection().get_selected()
        if not iter: return
        document = model.get_value(iter, 0)
        edw = EditDocumentNameWindow(self.path, document )
        result = edw.run()
        if result:
             self.treeview_default_document.get_model().set_value(iter, 0, edw.return_value)
             
    def on_toolbutton_document_delete_clicked(self, widget):
        model, iter = self.treeview_default_document.get_selection().get_selected()
        if not iter: return
        self.treeview_default_document.get_model().remove(iter)
        return


    # Customise the vhost properties window
    def load_vhost_properties(self, vhost):
        self.documents = []
        if vhost.config.ServerAdmin: self.entry_admin_email.set_text(vhost.config.ServerAdmin.value)
        if vhost.config.ErrorLog: self.entry_log_location.set_text(vhost.config.ErrorLog.value)
        if vhost.config.LogLevel:
            self.combobox_log_level.set_active( self.log_levels.index( vhost.config.LogLevel.value ) )
        if vhost.config.ServerSignature and vhost.config.ServerSignature.value.lower() != "off":
            self.checkbutton_server_signature.set_active(True)
        if vhost.config.DirectoryIndex:
            self.documents = list(vhost.config.DirectoryIndex.opts)

        self.update_tree()
        return
        
    # Perform action on vhost properties save
    def update_vhost_properties(self, vhost):
     
        if self.entry_admin_email.get_text(): vhost.config.ServerAdmin.value = self.entry_admin_email.get_text()
        if self.entry_log_location.get_text() : vhost.config.ErrorLog.value =  self.entry_log_location.get_text()
        vhost.config.LogLevel.value =  self.log_levels[ self.combobox_log_level.get_active() ]
        if self.checkbutton_server_signature.get_active():
             vhost.config.ServerSignature.value = "on"
        else:
             vhost.config.ServerSignature.value = "off"

        iter = self.treeview_default_document.get_model().get_iter_first()
        self.documents = []
        while 1:
            if not iter: break
            if self.treeview_default_document.get_model().get_value(iter, 0):
                self.documents.append( self.treeview_default_document.get_model().get_value(iter, 0) )
            iter = self.treeview_default_document.get_model().iter_next(iter)
        vhost.config.DirectoryIndex.opts = self.documents
        
        if len(self.documents) == 0:
            del vhost.config.DirectoryIndex

        server_admin = self.entry_admin_email.get_text()
        return True, None

def register( path ):
    return AdvancedVhostPlugin( path )

