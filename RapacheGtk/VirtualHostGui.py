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

        
class VirtualHostWindow:
    
    def __init__ ( self, parent = None):
           
        self.vhost = None
        self.parent = parent
        self.plugins = []

        gladefile = os.path.join(Configuration.GLADEPATH, "edit_vhost.glade")
        wtree = gtk.glade.XML(gladefile)
        
        self.window = wtree.get_widget("dialog_edit_vhost")
        self.entry_domain = wtree.get_widget("entry_domain")
        self.entry_location = wtree.get_widget("entry_location")
        self.button_location = wtree.get_widget("button_location")
        self.treeview_domain = wtree.get_widget("treeview_domain")
        self.checkbutton_hosts = wtree.get_widget("checkbutton_hosts")
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
        
        signals = {
            "on_toolbutton_domain_add_clicked"       : self.on_toolbutton_domain_add_clicked,
            "on_toolbutton_domain_edit_clicked"     : self.on_toolbutton_domain_edit_clicked,
            "on_toolbutton_domain_delete_clicked"   : self.on_toolbutton_domain_delete_clicked,
            "on_button_save_clicked"            : self.on_button_save_clicked,
            "on_button_cancel_clicked"          : self.on_button_cancel_clicked,
            "on_entry_domain_changed"              : self.on_entry_domain_changed,
            "on_button_location_clicked"        : self.on_button_location_clicked,
            "on_entry_domain_focus_out_event"    : self.on_entry_domain_focus_out_event,
            "on_button_location_clear_clicked"    : self.on_button_location_clear_clicked,
            "on_button_restore_version_clicked" : self.on_button_restore_version_clicked,
            "on_linkbutton_documentation_clicked" : self.on_linkbutton_documentation_clicked,
            "on_notebook_switch_page" : self.on_notebook_switch_page
        }
        wtree.signal_autoconnect(signals)
        
        self.combobox_vhost_backups.set_active(0)
        
        self.text_view_vhost_source = GuiUtils.new_apache_sourceview()
        wtree.get_widget( 'text_view_vhost_source_area' ).add( self.text_view_vhost_source )
        self.text_view_vhost_source.show()
        
        # add on destroy to quit loop
        self.window.connect("destroy", self.on_destroy)
        
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
        
        for plugin in self.parent.plugin_manager.plugins:
        	try:
        	    if plugin.is_enabled():      	        
        	        plugin.init_vhost_properties(self.notebook)
    	        	self.plugins.append(plugin)
        	except Exception:
        		traceback.print_exc(file=sys.stdout)
        
    def on_notebook_switch_page(self, notebook, page, page_num):
        # Assume for now it always page number 1
        if page_num == 1:
            # how to update this.....
            self.save()
            buf = self.text_view_vhost_source.get_buffer()
            text = self.vhost.get_source_generated(  buf.get_text(buf.get_start_iter(), buf.get_end_iter() ) )
            # TODO: Remove this line !! hack to stop double ups from parser
            text = text.replace("\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
            buf.set_text( text )
            buf.set_modified(False) 
            pass
        else:
            self.reload()

    def on_linkbutton_documentation_clicked(self, widget):
        print widget.get_uri()
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
            # load default  
            site = VirtualHostModel( "", self.parent.plugin_manager)

        self.window.show()           
        gtk.main()

    def load (self, name ):

        self.vhost = VirtualHostModel( name, self.parent.plugin_manager )

        self._load()
        
        for file in self.vhost.get_backup_files():
            self.combobox_vhost_backups.append_text("Backup " + file[0][-21:-4])

        self.label_path.set_text("File : " + self.vhost.get_source_filename() ) 
         
    def reload(self):
    
        buf = self.text_view_vhost_source.get_buffer()
        try:
            self.vhost.load_from_string( buf.get_text(buf.get_start_iter(), buf.get_end_iter()), self.parent.plugin_manager)
        except "VhostUnparsable":            
            pass     
         
        self._load()
        
    def _load(self):
        print "load"
        try:
            #self._get( 'has_www' ).set_active( site.data[ 'has_www' ] )
            server_name = self.vhost.data[ 'ServerName' ] 
            if ( server_name != None ):
                self.entry_domain.set_text( server_name )
            document_root = self.vhost.data[ 'DocumentRoot' ] 
            if ( document_root != None ):
                self.entry_location.set_text( document_root )
            server_alias = None
            if (self.vhost.data.has_key("ServerAlias")):
                server_alias = self.vhost.data[ 'ServerAlias' ]
            self.treeview_domain_store.clear()
            if ( server_alias != None ): 
                for domain in server_alias:
                    self.treeview_domain_store.append((domain, None))            
            print self.vhost.data
        except "VhostUnparsable":            
            pass
        
        for plugin in self.parent.plugin_manager.plugins:
        	try:
        	    if plugin.is_enabled():          
        	        plugin.load_vhost_properties(self.vhost)
    	        	self.plugins.append(plugin)
        	except Exception:
        		traceback.print_exc(file=sys.stdout)

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

        # auto create a www entry
        #if not force_domain and domain and len(self.treeview_domain_store) == 0 and not domain.startswith("www"):
        #    self.treeview_domain_store.append(("www." + domain, None))

    def on_entry_domain_focus_out_event(self, widget, opt):
        self.set_default_values_from_domain()
        
    def on_entry_domain_changed(self, unused_widget = None):
        widget = self.entry_domain
        name = widget.get_text()
        if ( valid_domain_name( name ) ):
            self.button_save.set_sensitive(True);
            #if self.create_new :
            #    self.xml.get_widget( 'default_folder' ).set_text( '/var/www/'+name+'/httpdocs' )
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
        print domain
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
        res = self.save()
        
        # save over buffer content
        buf = self.text_view_vhost_source.get_buffer()
        text = self.vhost.get_source_generated(  buf.get_text(buf.get_start_iter(), buf.get_end_iter() ) )
        self.vhost.save(text)
        
        # check apache config
        returncode, error = self.parent.apache.test_config()
        if not returncode:
            error = error.strip().split(":")
            error = ":".join(error[2:])
            md = gtk.MessageDialog(self.window, flags=0, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK_CANCEL, message_format=error + "\n\nAre you sure you want to continue, apache will not start until all errors are resolved")
            result = md.run()
            md.destroy()
            if result != gtk.RESPONSE_OK:
                return

        #self.parent.create_vhost_list()        
        self.parent.refresh_vhosts()
        self.parent.please_restart()
        self.window.destroy()
        
    def save(self):
        result = True

        if self.entry_location.get_text() == "" and self.vhost.is_new:
            self.set_default_values_from_domain( True )
        
        self.vhost.data[ 'ServerName' ] = self.entry_domain.get_text()
        self.vhost.data[ 'DocumentRoot' ] = self.entry_location.get_text()
        self.vhost.data[ 'ServerAlias' ] = self.get_server_aliases_list()
        
        self.hack_hosts = self.checkbutton_hosts.get_active()      
        
	    # Save plugins

        if self.plugins:
            for plugin in self.plugins:
                try:
                    if plugin.is_enabled():
                        res, message = plugin.save_vhost_properties(self.vhost)
                        if not res:
                            self.show_error ( message )
                            result = False
                except Exception:
                    traceback.print_exc(file=sys.stdout) 
        return result
                       
    def on_button_cancel_clicked(self, widget):
        self.window.destroy()
        return    
    def show_error ( self, message ):
        
        self.message_text.set_label( '<b>'+message+'</b>' )
        self.error_area.show()                 

