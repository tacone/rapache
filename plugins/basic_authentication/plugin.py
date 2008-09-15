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
from RapacheCore import Shell
from htpasswd import Htpasswd
from user_credentials import UserCredentials
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

class BasicAuthenticationPlugin(PluginBaseObject):

    def __init__(self, path):
        
        # The path to the plugin
        self.path = path
    
        # module this plugin works with
        self.module = "auth_basic"
        
        # Define what additional config should be read from vhost file
        self.vhosts_config = { "AuthType" : 0, "AuthName" : 0, "AuthUserFile" : 0, "Require" : 1 } # 0 value | 1 options
        
        self.default_location = "/etc/apache2/basic-auth/passwords"
        
        self.users = Htpasswd()
        self.users_active = []
    
    def treeview_users_toggled(self, cell, path):
        # toggle check box value
        iter = self.treeview_users_store.get_iter((int(path),))
        self.treeview_users_store.set_value(iter, 0, not self.treeview_users_store.get_value(iter, 0))
        return
            
    def on_toolbutton_user_add_clicked(self, widget):
        uc = UserCredentials(self.path)
        result= uc.run()
        
        if result:
            self.users.update( result[0], result[1] )
            self.users_active.append( result[0] )
            self.update_users()
        
        return       
        
    def on_toolbutton_user_edit_clicked(self, widget):

        model, iter = self.treeview_users.get_selection().get_selected()
        if not iter: return
        username = model.get_value(iter, 2)

        uc = UserCredentials(self.path)
        uc.load( username )
        result = uc.run()
        
        if result:
            self.users.update( result[0], result[1] )
            self.users_active.append( result[0] )
            self.update_users()

        return         
        
    def on_toolbutton_user_delete_clicked(self, widget):
        
        model, iter = self.treeview_users.get_selection().get_selected()
        if not iter: return
        username = model.get_value(iter, 2)
        
        md = gtk.MessageDialog(None, flags=0, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL, message_format="Are you sure you want to delete '"+ username+"' ?") 
        result = md.run()
        md.destroy()
        if result == gtk.RESPONSE_OK:
            self.users.delete(username)
            self.update_users()

        return          
        
    def on_treeview_users_row_activated(self, a,b,c):
        model, iter = self.treeview_users.get_selection().get_selected()
        if not iter: return
        username = model.get_value(iter, 2)

        uc = UserCredentials(self.path)
        uc.load( username )
        result = uc.run()
        
        if result:
            self.users.update( result[0], result[1] )
            self.users_active.append( result[0] )
            self.update_users()
        
        
    def on_button_location_clear_clicked(self, widget):
        return None          
        
    def update_users(self):
        self.treeview_users_store = gtk.ListStore(bool, str, str)
        self.treeview_users.set_model(self.treeview_users_store)   

        for user in self.users.entries:
            self.treeview_users_store.append((user[0] in self.users_active , user[0], user[0]))         
        
        
    def init_vhost_properties(self):

        # Get glade file XML
        f = open( os.path.join(self.path, "basic_auth.glade") ,"r")
        self.glade_vhost_xml =  f.read()
        f.close()

        wtree = gtk.glade.xml_new_from_buffer(self.glade_vhost_xml, len(self.glade_vhost_xml), "hbox_auth_basic")
        hbox_auth_basic = wtree.get_widget("hbox_auth_basic") 
        
        self.checkbutton_enable_auth_basic = wtree.get_widget("checkbutton_enable_auth_basic") 
        self.entry_warning_message = wtree.get_widget("entry_warning_message") 
        self.treeview_users = wtree.get_widget("treeview_users") 
        self.entry_location = wtree.get_widget("entry_location")      
        
        signals = {
            "on_toolbutton_user_add_clicked"    : self.on_toolbutton_user_add_clicked,
            "on_toolbutton_user_edit_clicked"   : self.on_toolbutton_user_edit_clicked,
            "on_toolbutton_user_delete_clicked" : self.on_toolbutton_user_delete_clicked,
            "on_treeview_users_row_activated"   : self.on_treeview_users_row_activated,
            "on_button_location_clear_clicked"  : self.on_button_location_clear_clicked
        }
        wtree.signal_autoconnect(signals)  
        
        # Setup tree
        column = gtk.TreeViewColumn((''))
        column.set_spacing(4)
        cell = gtk.CellRendererToggle()
        cell.connect('toggled', self.treeview_users_toggled)
        column.pack_start(cell, False)
        column.set_attributes(cell, active=0)
        self.treeview_users.append_column(column)

        column = gtk.TreeViewColumn(('User'))
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=1)
        self.treeview_users.append_column(column)

        self.entry_location.set_text(self.default_location)
        self.users.load(Shell.command.read_file(self.default_location))
        self.entry_warning_message.set_text("Enter your password")
        

        self.update_users()
        
        icon_theme = gtk.icon_theme_get_default()
        pixbuf = icon_theme.lookup_icon("gtk-dialog-authentication", 24, 0).load_icon()

        return hbox_auth_basic, "Basic Security", pixbuf

    # Customise the vhost properties window
    def load_vhost_properties(self, vhost):
        self.users_active = []
        self.checkbutton_enable_auth_basic.set_active(False)
        
        ds = vhost.config.Directory.search(  [vhost.get_document_root()]  )

        if len(  ds    ) > 0:
            d = ds[0]
            if d.AuthType:
                self.checkbutton_enable_auth_basic.set_active(d.AuthType.value.lower() == "basic")
                
            # only load if value changes
            if d.AuthUserFile:
                if d.AuthUserFile.value != self.entry_location.get_text():
                    self.entry_location.set_text(d.AuthUserFile.value)
                    content = Shell.command.read_file(self.entry_location.get_text())
                    if content:
                        self.users.load( content )
        
            if d.AuthName:
                self.entry_warning_message.set_text(d.AuthName.value)
                
            if d.Require:
                self.users_active = list(d.Require.opts)[1:]
                self.update_users()
                
        return True, None


    # Perform action on vhost properties update request
    def update_vhost_properties(self, vhost):
        
        self.users_active = []
        iter = self.treeview_users_store.get_iter_first()
        while 1:
            if not iter: break
            if self.treeview_users_store.get_value(iter, 0):
                self.users_active.append( self.treeview_users_store.get_value(iter, 2) )
            iter = self.treeview_users_store.iter_next(iter)
        
        ds = vhost.config.Directory.search(  [vhost.get_document_root()]  )
        d = None
        if len(ds) == 0:
            d = vhost.config.sections.create("Directory", vhost.get_document_root())
        else:
            d = ds[0]
        
        if self.checkbutton_enable_auth_basic.get_active() and len(self.users_active) > 0:
            d.AuthType.value = "Basic"
            
            if self.entry_warning_message.get_text():
                d.AuthName.value = self.entry_warning_message.get_text() 
            elif d.AuthName:
                del d.AuthName
                
            d.AuthUserFile.value =  self.entry_location.get_text()
            d.Require.opts = ["user"] + self.users_active
            
        else:
            if d.AuthType : del d.AuthType
            if d.AuthName : del d.AuthName
            if d.AuthUserFile : del d.AuthUserFile
            if d.Require : del d.Require

        return True, None


    # Perform action on vhost properties save
    def save_vhost_properties(self, vhost):

        Shell.command.write_file( self.entry_location.get_text(), self.users.save())
        
        return True, None


def register( path ):
    return BasicAuthenticationPlugin( path )

