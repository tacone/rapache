#!/usr/bin/env python

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

""".
Issues with the new window:
    - self.parent doesn't work
    - onblur doesn't trigger when pressing Return
    - changing a domain name doesn't change subdomains
    - empty server aliases shuoldn't be managed
ALSO:
    - please implement a delete directive func in the parser
    - move denorm. vhosts in another tab
    - merge with Qense warning window
"""

import sys
import re


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

import os
import pango
import tempfile
import traceback
import RapacheGtk.GuiUtils
from RapacheCore.VirtualHost import *
from RapacheGtk import GuiUtils
from EditDomainNameGui import EditDomainNameWindow
import RapacheGtk.DesktopEnvironment as Desktop

class UnexpectedCase( Exception ):        
    pass
    
class VirtualHostWindow:
    
    def __init__ ( self, parent = None):
           
        
        self.parent = parent
        self.plugins = []
        self.vhost = None

        gladefile = os.path.join(Configuration.GLADEPATH, "edit_vhost.glade")
        wtree = gtk.glade.XML(gladefile)
        
        self.window = wtree.get_widget("dialog_edit_vhost")
        self.entry_domain = wtree.get_widget("entry_domain")
        self.entry_location = wtree.get_widget("entry_location")
        self.button_location = wtree.get_widget("button_location")
        self.treeview_domain = wtree.get_widget("treeview_domain")
        self.checkbutton_hosts = wtree.get_widget("checkbutton_hosts")
        self.label_hosts = wtree.get_widget("label_hosts")
        self.toolbutton_domain_add = wtree.get_widget("toolbutton_domain_add")
        self.toolbutton_domain_edit = wtree.get_widget("toolbutton_domain_edit")
        self.toolbutton_domain_delete = wtree.get_widget("toolbutton_domain_delete")
        self.combobox_vhost_backups = wtree.get_widget("combobox_vhost_backups")
        self.notebook = wtree.get_widget("notebook")
        self.button_save = wtree.get_widget("button_save")
        self.error_area = wtree.get_widget("error_area")
        self.label_path = wtree.get_widget("label_path")
        self.message_text = wtree.get_widget("message_text")
        self.error_area = wtree.get_widget("error_area")
        self.treeview_menu = wtree.get_widget("treeview_menu")
        signals = {
            "on_toolbutton_domain_add_clicked"  : self.on_toolbutton_domain_add_clicked,
            "on_toolbutton_domain_edit_clicked" : self.on_toolbutton_domain_edit_clicked,
            "on_toolbutton_domain_delete_clicked": self.on_toolbutton_domain_delete_clicked,
            "on_button_save_clicked"            : self.on_button_save_clicked,
            "on_button_cancel_clicked"          : self.on_button_cancel_clicked,
            "on_entry_domain_changed"           : self.on_entry_domain_changed,
            "on_button_location_clicked"        : self.on_button_location_clicked,
            "on_entry_domain_focus_out_event"   : self.on_entry_domain_focus_out_event,
            "on_button_location_clear_clicked"  : self.on_button_location_clear_clicked,
            "on_button_restore_version_clicked" : self.on_button_restore_version_clicked,
            "on_linkbutton_documentation_clicked" : self.on_linkbutton_documentation_clicked,
            "on_notebook_switch_page"           : self.on_notebook_switch_page,
            "on_treeview_menu_cursor_changed"   :   self.on_treeview_menu_cursor_changed,
            "on_button_error_close_clicked"     : self.on_button_error_close_clicked
        }
        wtree.signal_autoconnect(signals)
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)  
        
        self.combobox_vhost_backups.set_active(0)
        
        self.text_view_vhost_source = GuiUtils.new_apache_sourceview()
        wtree.get_widget( 'text_view_vhost_source_area' ).add( self.text_view_vhost_source )
        self.text_view_vhost_source.show()
        
        # Setup tree
        column = gtk.TreeViewColumn(('Domains'))
        column.set_spacing(4)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=0)
        self.treeview_domain.append_column(column)
        
        self.treeview_domain_store = gtk.ListStore(str, object)
        self.treeview_domain.set_model(self.treeview_domain_store)

        GuiUtils.style_as_tooltip( self.error_area )
        self.on_entry_domain_changed()
        
        
        #Setup Menu Tree
        column = gtk.TreeViewColumn(('Icon'))
        column.set_spacing(4)
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, expand=False)
        column.set_attributes(cell, pixbuf=0)
        self.treeview_menu.append_column(column)
        
        column = gtk.TreeViewColumn(('Title'))
        column.set_spacing(4)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=1)
        self.treeview_menu.append_column(column)
        
        store = gtk.ListStore(gtk.gdk.Pixbuf, str, int)
        self.treeview_menu.set_model(store)  
        
        icon_theme = gtk.icon_theme_get_default()
        store.append((icon_theme.lookup_icon("applications-internet", 24, 0).load_icon(), "Domain", 0))  
        
        # init enabled plugins
        for plugin in self.parent.plugin_manager.plugins:
        	try:
        	    if plugin.is_enabled():      	        
        	        content, title, pixbuf = plugin.init_vhost_properties()
        	        tab_count = self.notebook.get_n_pages() - 1
        	        plugin._tab_number = self.notebook.insert_page(content, gtk.Label(title), tab_count)
        	        store.append((pixbuf, title, tab_count))
        	        content.show()
    	        	self.plugins.append(plugin)
        	except Exception:
        		traceback.print_exc(file=sys.stdout)
        		
        store.append((icon_theme.load_icon(gtk.STOCK_EDIT, 24, 0), "Definition File", self.notebook.get_n_pages() - 1))  
        
        select = self.treeview_menu.get_selection()
        select.select_path(0)
        
        
        self.__previous_active_tab = 0
        
        self.accel_group = gtk.AccelGroup()
        self.window.add_accel_group(self.accel_group)
        
        self.button_save.add_accelerator("clicked", self.accel_group, 13, 0, 0)

        self.vhost =  VirtualHostModel( "")
        
    def on_treeview_menu_cursor_changed(self, widget):
        model, iter =  self.treeview_menu.get_selection().get_selected()
        if not iter: return
        page_number = model.get_value(iter, 2)
        
        # Save 
        result = True
        error = ""
        if self.__previous_active_tab == self.notebook.get_n_pages() - 1:
            result, error =  self.save_edit_tab()
        elif self.__previous_active_tab == 0:
            self.save_domain_tab()
            result = True
        else:
            result, error = self.save_plugin_tab(self.__previous_active_tab)
        
        # process     
        if not result:
            self.show_error("Sorry can not change tabs, " + error)
            select = self.treeview_menu.get_selection()
            select.select_path((self.__previous_active_tab))
            return

        self.clear_error()
        
        # Load
        if page_number == self.notebook.get_n_pages() - 1:
            self.load_edit_tab()
        elif page_number == 0:
            self.load_domain_tab()    
        else:
            self.update_plugin_tab(page_number)

        self.window.set_title("VirtualHost Editor - " + self.vhost.get_server_name() )

        self.__previous_active_tab = page_number
        self.notebook.set_current_page(page_number)  

    def on_notebook_switch_page(self, notebook, page, page_num):
       return

    def on_linkbutton_documentation_clicked(self, widget):
        Desktop.open_url( widget.get_uri() )
        
    def on_button_restore_version_clicked(self, widget):
        buf = self.text_view_vhost_source.get_buffer()
        if buf.get_modified():
            md = gtk.MessageDialog(self.window, flags=0, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL, message_format="Are you sure, you will lose all your current changes")
            result = md.run()
            md.destroy()
            if result != gtk.RESPONSE_OK:
                return
        
        selected = self.combobox_vhost_backups.get_active()
        
        if selected == 0:
            buf.set_text( self.vhost.get_source() )
        else:
            value = self.combobox_vhost_backups.get_active_text()[7:]
            buf.set_text( self.vhost.get_source_version(value) )
            
        buf.set_modified(False)
        
        
    def run(self):

        # Load UI Plugins
        if self.vhost:
            site = self.vhost
        else:        
            #this should never happen since now we initialize an empty VirtualHostModel
            #inside __init__
            raise UnexpectedCase,  "Internal error, existing VirtualHostModel expected"
            pass
            

        self.window.show()   
                
        gtk.main()

    def load (self, vhost ):
        if vhost:
            self.vhost = vhost
            #hosts tooggling not supported on editing
            self.checkbutton_hosts.hide()
            self.label_hosts.hide()
        else:
            self.checkbutton_hosts.set_active(True)
        self.load_domain_tab()
        
        for file in self.vhost.get_backup_files():
            self.combobox_vhost_backups.append_text("Backup " + file[0][-21:-4])

        self.label_path.set_text( self.vhost.get_source_filename() ) 
        self.on_entry_domain_changed()
        
    def save_edit_tab(self):
        #print "Save edit tab"
        buf = self.text_view_vhost_source.get_buffer()
        content = buf.get_text(buf.get_start_iter(), buf.get_end_iter())

        return self.vhost.load_from_string( content ), "your edited source does not seem to be valid syntax"

    def load_edit_tab(self):
        #print "load edit tab"
        # open edit tab update content
        buf = self.text_view_vhost_source.get_buffer()
        text = self.vhost.get_source_generated()
        buf.set_text( text )
        buf.set_modified(False) 
        
    def load_domain_tab(self):
        #print "Load domain tab"
        
        vhost_name = self.vhost.get_server_name()
        self.window.set_title("VirtualHost Editor - " + vhost_name )
        self.window.set_icon_from_file(self.vhost.get_icon())
        
        modal = self.treeview_menu.get_model()
        iter = modal.get_iter(0)
        
        modal.set_value(iter, 0, self.window.get_icon())
        server_name = ''
        if self.vhost.config and self.vhost.config.servername and self.vhost.config.servername.value:
            server_name = self.vhost.config.servername.value
            
        self.entry_domain.set_text( server_name )
        """ ???    
        if not self.vhost.is_default():            
            self.entry_domain.set_text( server_name )
        elif self.vhost.config.ServerName:
            self.entry_domain.set_sensitive(False)
        """
        
        document_root = self.vhost.get_document_root()
        if ( document_root != None ):
            self.entry_location.set_text( document_root )
        server_alias = None
        
        self.treeview_domain_store.clear()

        server_alias = self.vhost.get_server_alias()
        if server_alias:
            for domain in server_alias:
                self.treeview_domain_store.append((domain, None))   

    def save_domain_tab(self):
        #print "Save domain tab"
        if self.entry_location.get_text() == "" and self.vhost.is_new:
            self.set_default_values_from_domain( True )
        
        #if not self.vhost.is_default():
        if self.entry_domain.get_text():
            self.vhost.config.ServerName.value = self.entry_domain.get_text()
        elif self.vhost.config.ServerName:
            del self.vhost.config.ServerName 
            
        self.window.set_title("VirtualHost Editor - " + self.vhost.get_server_name() )
        
        if self.vhost.config.DocumentRoot:
            old_document_root = self.vhost.config.DocumentRoot.value
            if old_document_root != self.entry_location.get_text():
                ds = self.vhost.config.Directory.search( [old_document_root] )
                if len(ds) > 0:
                    d = ds[0]
                    d.value = self.entry_location.get_text()
        self.vhost.config.DocumentRoot.value = self.entry_location.get_text()

        aliases = self.get_server_aliases_list()
        if len(aliases) > 0:
            self.vhost.config.ServerAlias.opts = self.get_server_aliases_list()
        elif self.vhost.config.ServerAlias:
            del self.vhost.config.ServerAlias
             
        self.hack_hosts = self.checkbutton_hosts.get_active()      

        return
        
    def update_plugin_tab(self, tab):
        #print "Update plugin : ", tab
        if self.plugins:
            for plugin in self.plugins:
            	try:
            	    if plugin.is_enabled() and plugin._tab_number == tab:          
            	        plugin.load_vhost_properties(self.vhost)
            	except Exception:
            		traceback.print_exc(file=sys.stdout)

    def save_plugin_tab(self, tab):
        result = True
        error = ""
        #print "Save plugin : ", tab
        if self.plugins:
            for plugin in self.plugins:
                try:
                    if plugin.is_enabled() and plugin._tab_number == tab:  
                        result, error = plugin.update_vhost_properties(self.vhost)
                except Exception:
            		traceback.print_exc(file=sys.stdout)
        return result, error
                 
    def get_domain (self):
        return self.entry_domain.get_text().strip()
        #url.lower().startswith('http://')
        #url[7:]
    def set_default_values_from_domain(self, force_domain=False):
        domain = self.get_domain()
        
        # auto set the location
        if domain and (not self.entry_location.get_text() or force_domain):
            self.entry_location.set_text( "/var/www/%s" % (domain +"/httpdocs" ))
        if force_domain and not domain:
            self.entry_location.set_text("")

    def on_entry_domain_focus_out_event(self, widget, opt):
        self.set_default_values_from_domain()
        
    def on_entry_domain_changed(self, unused_widget = None):
        widget = self.entry_domain
        name = widget.get_text()                
        if valid_domain_name( name ) or (self.vhost and self.vhost.is_default()):
            self.button_save.set_sensitive(True);
        else:
            self.button_save.set_sensitive(False); 
    
    def on_button_location_clear_clicked(self, widget):
        self.set_default_values_from_domain(True)


    def on_button_location_clicked(self, widget):
        chooser = gtk.FileChooserDialog(
            title=None,
            action=gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER,
                        buttons=(gtk.STOCK_CANCEL,
                        gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN,
                        gtk.RESPONSE_OK))
                        
        location = self.entry_location.get_text().strip()
        
        while not Shell.command.exists(location):
            location = os.path.abspath(os.path.join(location, os.path.pardir))
        
        if not location:
            location = "/var/www"    
        chooser.set_current_folder(location)
        response = chooser.run()
        
        if response == gtk.RESPONSE_OK:
            self.entry_location.set_text( chooser.get_filename() )
        chooser.destroy()

    def on_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_toolbutton_domain_add_clicked(self, widget):
        edw = EditDomainNameWindow(self.entry_domain.get_text().strip())
        domain = edw.run()
        if domain:
            self.treeview_domain_store.append((domain, None))
        return
        
    def  get_server_aliases_list (self ):
        aliases = []
        for row in self.treeview_domain_store: aliases.append( row[0] )
        return aliases
    def on_toolbutton_domain_edit_clicked(self, widget):
    
        model, iter = self.treeview_domain.get_selection().get_selected()
        if not iter: return
        domain = model.get_value(iter, 0)

        edw = EditDomainNameWindow( domain )
        result = edw.run()
        if result:
            self.treeview_domain_store.set_value(iter, 0, edw.return_value)
        return     
             
    def on_toolbutton_domain_delete_clicked(self, widget):
        model, iter = self.treeview_domain.get_selection().get_selected()
        if not iter: return
        self.treeview_domain_store.remove(iter)
        return  
            
    def on_button_save_clicked(self, widget):

        # Save
        result, error = True, ""
        if self.__previous_active_tab == self.notebook.get_n_pages() - 1:
            result, error = self.save_edit_tab()
        elif self.__previous_active_tab == 0:
            self.save_domain_tab()
        else:
            result, error = self.save_plugin_tab(self.__previous_active_tab)
        
        # if errors
        if not result:
            md = gtk.MessageDialog(self.window, flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=error)
            result = md.run()
            md.destroy()
            return 
    
        # All plugins on save
        if self.plugins:
            for plugin in self.plugins:
                try:
                    if plugin.is_enabled():
                        res, message = plugin.save_vhost_properties(self.vhost)
                        if not res:
                            result = False
                            if tab_number and plugin._tab_number == tab_number:
                                self.show_error ( message )
                except Exception:
                    traceback.print_exc(file=sys.stdout) 
        

        is_new = self.vhost.is_new
        # save over buffer content
        self.vhost.save()
        
        #update /etc/hosts only if it's a new vhost
        
        if is_new:
            if self.hack_hosts:
                #update servername
                if self.vhost.config.ServerName and self.vhost.config.ServerName.value:
                    Shell.command.sudo_execute ( [os.path.join(Configuration.APPPATH, "hosts-manager"), '-a', self.vhost.config.ServerName.value ] )
                #add an entry for each host
                if self.vhost.config.ServerAlias:
                    for alias in self.vhost.config.ServerAlias:
                        Shell.command.sudo_execute ( [os.path.join(Configuration.APPPATH, 'hosts-manager'), '-a', alias ])
                    
        # check apache config
        returncode, error = self.parent.apache.test_config()
        if not returncode:
            error = error.strip()
            md = gtk.MessageDialog(self.window, flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK_CANCEL, message_format="Changes have been saved, but an error has been detected: \n\n"+error + "\n\nAre you sure you want to continue? Apache may not start until all errors are resolved.")
            result = md.run()
            md.destroy()
            if result != gtk.RESPONSE_OK:
                return

        #self.parent.create_vhost_list()        
        self.parent.refresh_vhosts()
        self.parent.please_restart()
        self.window.destroy()
                               
    def on_button_cancel_clicked(self, widget):
        self.window.destroy()
        return    
        
    def on_button_error_close_clicked(self, widget):
        self.clear_error()
                
    def show_error ( self, message ):
        self.message_text.set_label( '<b>'+message+'</b>' )
        self.error_area.show() 
                        
    def clear_error ( self):
        self.error_area.hide()  
