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
        
class VirtualHostWindow:
    
    def __init__ ( self, parent = None):
           
        self.vhost = None
        self.create_new = True
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
        self.notebook = wtree.get_widget("notebook")
        self.button_save = wtree.get_widget("button_save")
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
            "on_button_location_clear_clicked"    : self.on_button_location_clear_clicked
        }
        wtree.signal_autoconnect(signals)
        
        self.text_view_vhost_source = GuiUtils.new_apache_sourceview()
        wtree.get_widget( 'text_view_vhost_source_area' ).add( self.text_view_vhost_source )
        self.text_view_vhost_source.set_editable( False )
        self.text_view_vhost_source.show()
                
        self.notebook.get_nth_page( 1 ).hide()
        self.notebook.get_nth_page( 2 ).hide()
        
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
        
    def run(self):

        # Load UI Plugins
        if self.vhost:
            site = self.vhost
        else:
            # load default  
            site = VirtualHostModel( "", self.parent.plugin_manager)
            
        for plugin in self.parent.plugin_manager.plugins:
        	try:
        	    if plugin.is_enabled():      	        
        	        plugin.load_vhost_properties(self.notebook, site.data)
    	        	self.plugins.append(plugin)
        	except Exception:
        		traceback.print_exc(file=sys.stdout)

        self.window.show()           
        gtk.main()

    def load (self, name ):
        self.vhost = VirtualHostModel( name )
        self.create_new = False
        try:
            self.vhost.load(False, self.parent.plugin_manager)
            print self.vhost.data
            #self._get( 'has_www' ).set_active( site.data[ 'has_www' ] )
            server_name = self.vhost.data[ 'ServerName' ] 
            if ( server_name != None ):
                self.entry_domain.set_text( server_name )
            document_root = self.vhost.data[ 'DocumentRoot' ] 
            if ( document_root != None ):
                self.entry_location.set_text( document_root )
            server_alias = self.vhost.data[ 'ServerAlias' ]
            if ( server_alias != None ): 
                for domain in server_alias:
                    self.treeview_domain_store.append((domain, None))            
            print self.vhost.data
        except "VhostUnparsable":            
            pass
        
        buf = self.text_view_vhost_source.get_buffer()
        buf.set_text( self.vhost.get_source() )
        


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
        if self.entry_location.get_text() == "" and self.create_new:
            self.set_default_values_from_domain( True )
        
        options = {}
        options[ 'ServerAlias' ] =  []
        options[ 'ServerName' ] = self.entry_domain.get_text()
        options[ 'hack_hosts' ] = self.checkbutton_hosts.get_active()                
        options[ 'DocumentRoot' ] = self.entry_location.get_text()
        options[ 'ServerAlias' ] = self.get_server_aliases_list()

	    # Save plugins
        if self.plugins:
            for plugin in self.plugins:
                try:
                    if plugin.is_enabled():
                        plugin.save_vhost_properties(options)
                except Exception:
                    traceback.print_exc(file=sys.stdout) 

        print options
        
        try:
            if ( self.create_new ):
                site = VirtualHostModel( options[ 'ServerName' ] )
                site.create ( options )
            else:
                name = self.vhost.data['name']
                print "Current name:", name
                site = VirtualHostModel( name )
                site.update( options, name )

            
            #self.parent.create_vhost_list()        
            self.parent.refresh_vhosts()
            self.parent.please_restart()
            self.window.destroy()
        except "VhostExists":
           print "========================"
           self.show_error( "A virtual host with the same name already exists" )     
        
                         
    def on_button_cancel_clicked(self, widget):
        self.window.destroy()
        return    
    def show_error ( self, message ):
        
        self.xml.get_widget( 'message_text' ).set_label( '<b>'+message+'</b>' )
        self.xml.get_widget( 'message_container' ).show()                 

