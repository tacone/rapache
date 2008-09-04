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

#TODO throw appropriate exceptions (bug: vhost already exist displays only 
# after actually trying to create it's dir. check before )

#TODO read ERRORLEVEL from command line operations
#TODO stop operation if gksudo fails
#TODO check for sites-enabled-only sites and normalize them

#TODO delete-tarantella: hosts deletion & confirmation

#TODO refuse to edit complex vhosts ( done ? )

#import gnome.ui
import gobject
import gtk
import os
import re
import threading
import time
import copy


from RapacheGtk.VirtualHostGui import VirtualHostWindow
from RapacheGtk.ModuleGui import ModuleWindow
from RapacheCore.PluginManager import PluginManager
from RapacheGtk.ModuleGui import open_module_doc
from RapacheCore.VirtualHost import *
from RapacheCore.Apache import Apache2
from RapacheGtk import ConfirmationWindow
from RapacheGtk import GuiUtils
from RapacheCore import Shell
import VhostsTreeView
import RapacheCore.Observer
from RapacheGtk.EventDispatcher import Master
import subprocess
import RapacheGtk.DesktopEnvironment as Desktop
import traceback
data = \
[(False, "Loading", "please wait" )]

APPNAME="Rapache"
APPVERSION="0.6"

# Turn on gtk threading
gtk.gdk.threads_init()

# Define threaded attribute
def threaded(f):
	def wrapper(*args):
		t = threading.Thread(target=f, args=args)
		t.setDaemon(True) # wont keep app alive
		t.start()
	return wrapper

class MainWindow( RapacheCore.Observer.Observable ) :
    """This is an Hello World Rapacheefication application"""
    
    def __init__(self, *args, **kwargs):
        super (MainWindow, self).__init__ (*args, **kwargs)
        Master.register(self)

        self.denormalized_virtual_hosts = {}
        self.plugin_manager = PluginManager()
        self.apache = Apache2()
        
        #gnome.init(APPNAME, APPVERSION)
        self.gladefile = Configuration.GLADEPATH + "/" + "main.glade"  
        self.xml = gtk.glade.XML(self.gladefile)         
        #Create our dictionary and connect it
        dic = { "new_button_clicked" : self.new_button_clicked,
            "on_MainWindow_destroy" : self.quit ,
            "please_restart" : self.restart_apache ,            
            "on_delete" : self.delete_button_clicked,
            "edit_button_clicked" : self.edit_button_clicked,
            "edit_module_button_clicked" : self.edit_module_button_clicked,
            "browse_sites_available" : self.browse_sites_available,
            "fix_vhosts_clicked" : self.fix_vhosts,
            "surf_this_button_clicked" : self.surf_this,
            "browse_button_clicked" : self.browse_this,
            "about_clicked" : self.display_about,
            "open_doc_button_clicked" : self.open_doc_button_clicked,
            "on_button_hide_warning_clicked" : self.on_button_hide_warning_clicked,
            "quit" : self.quit,
            "on_menuitem_stop_apache_activate" : self.on_menuitem_stop_apache_activate,
            "on_button_open_log_clicked" : self.on_button_open_log_clicked
        }
        
        gtk.window_set_default_icon_from_file(os.path.join( Configuration.GLADEPATH, 'icon_cadsoft_eagle_golden.svg'))
        
        self.xml.signal_autoconnect(dic)
        GuiUtils.change_button_label ( self.xml.get_widget( 'restart_apache' ), "Restart Apache" )
        #GuiUtils.change_button_label ( self.xml.get_widget( 'fix_vhosts' ), "Fix Virtual Hosts" )
        self.statusbar_server_status =  self.xml.get_widget( 'statusbar_server_status' )
        self.image_apache_status =  self.xml.get_widget( 'image_apache_status' )
        self.main_window = self.xml.get_widget("MainWindow")
        #hereby we create lists
        self.create_vhost_list()
        self.create_modules_list()
        self.create_errors_list()
        #hereby we fill them
        self.refresh_lists()
        
        GuiUtils.style_as_tooltip( self.xml.get_widget( 'restart_apache_notice' ) )
        #GuiUtils.style_as_tooltip( self.xml.get_widget( 'unnormalized_notice' ) )  
        #GuiUtils.style_as_tooltip( self.xml.get_widget( 'hbox_apache_config_error' ) )   
       
        # start status update
        self.statusbar_server_status_context_id = self.statusbar_server_status.get_context_id("Apache Server Status") 
        self.statusbar_server_status.push(self.statusbar_server_status_context_id, "Attempting to connect to server")
        self.update_server_status(True)
        
        
       
        
        self.menu_tools = self.xml.get_widget( 'menu_tools' )
        for plugin in self.plugin_manager.plugins:
        	try:
        	    if plugin.is_enabled():      	        
        	        menu_item = plugin.init_main_window(self)
                    if menu_item != None:
                        self.menu_tools.add(menu_item)
                        menu_item.show()
        	except Exception:
        		traceback.print_exc(file=sys.stdout)



        # Add rich edit to log
        self.text_view_log = GuiUtils.new_apache_sourceview()
        self.xml.get_widget( 'scroll_window_log' ).add( self.text_view_log )
        self.text_view_log.show()
        combobox_log = self.xml.get_widget( 'combobox_log' )
        files = Shell.command.listdir("/var/log/apache2")
        for file in files:
            if file.endswith(".log"):
                combobox_log.append_text(file)
        combobox_log.set_active(0)
        
    def on_button_open_log_clicked(self, widget):
        file = self.xml.get_widget( 'combobox_log' ).get_active_text()
        path = os.path.join("/var/log/apache2", file)
        text = Shell.command.read_file( path )
        self.text_view_log.get_buffer().set_text( text )
        self.text_view_log.set_editable(False)
        self.xml.get_widget( 'label_log_path').set_text( path )

    def refresh_config_test(self): 
        self.treeview_errors.load(self.apache)

    def add_new_vhost_menu_item(self, menu_item):
        new_button = self.xml.get_widget( 'new_button')
        menu = new_button.get_menu()
        
        if not menu:
            menu = gtk.Menu()
            new_button.set_menu( menu )
    
        menu.add(menu_item)
        menu.show_all()

    @threaded    
    def update_server_status(self, loop=False):
        window_status_icons = [ 
          # 0 - apache stopped
          os.path.join( Configuration.GLADEPATH, 'icon_cadsoft_eagle.svg' )
          # 1 - apache unreachable
         , os.path.join( Configuration.GLADEPATH, 'icon_cadsoft_eagle_orange.svg' ) #1
          # 2 - apache started
         , os.path.join( Configuration.GLADEPATH, 'icon_cadsoft_eagle_green.svg' ) #1
        ]
        
        while True:
            status = self.apache.get_status()
            text = "Apache is stopped"
            image = gtk.STOCK_NO

            # TODO: need ssh fail message here some where...

            if status == 1:
                text = "Warning can not contact apache"
                image = gtk.STOCK_DIALOG_WARNING
            if status == 2:
                text  = "Apache is running"   
                image = gtk.STOCK_YES
                
            gtk.gdk.threads_enter()
            self.image_apache_status.set_from_stock(image, gtk.ICON_SIZE_MENU)
            self.statusbar_server_status.pop(self.statusbar_server_status_context_id)
            self.statusbar_server_status.push(self.statusbar_server_status_context_id, text)
            gtk.gdk.threads_leave()
            
            self.main_window.set_icon_from_file(window_status_icons[status])
            
            if not loop:
                break
                
            time.sleep( Configuration.TEST_CONNECTION_INTERVAL )
            
    def on_menuitem_stop_apache_activate(self, widget):
        self.apache.stop()
        self.update_server_status()
        
    def on_button_hide_warning_clicked(self, widget):
        self.xml.get_widget( 'restart_apache_notice' ).hide()
        
    def handle_event(self, event ):
        if event.name == 'please_restart_apache':
            self.please_restart()
            return
        if event.name == 'please_reload_lists':
            self.load_lists()
            return
    def browse_sites_available(self, widget):
        Desktop.open_dir( Configuration.SITES_AVAILABLE_DIR )
        return
    
    def new_button_clicked(self, widget):
        new_vhost_window = VirtualHostWindow ( self )
        new_vhost_window.load("")
        new_vhost_window.run()
        self.refresh_config_test()
        
    def edit_button_clicked(self, widget, notused = None, notused2 = None):         
        vhost = self.vhosts_treeview.get_selected_line()
        self.open_edit_vhost_window( copy.deepcopy(vhost) )

        
    def open_edit_vhost_window(self, name):
        if ( self.is_vhost_editable( name ) == False ): return False
        new_vhost_window = VirtualHostWindow ( self )
        new_vhost_window.load( self.get_current_vhost() )
        new_vhost_window.run()    
        self.refresh_config_test()
        
    def delete_button_clicked( self, widget ):
        name = self.vhosts_treeview.get_selected_line()
        if ( self.is_vhost_editable( name ) == False ): return False
        if ( name == None ): return False
        result = ConfirmationWindow.ask_confirmation(           
            "You are about to delete the following domain: \n\n"+name+"\n\nData won't be recoverable. Proceed ?"
            ,'VirtualHost deletion' )
        if ( result != True ): return False
        site = VirtualHostModel( name )
        site.delete()
        self.vhosts_treeview.load()
        self.please_restart()
        self.refresh_config_test()
        
    def edit_module_button_clicked(self, widget, notused = None, notused2 = None):
        name = self.modules_treeview.get_selected_line()
        if ( self.is_module_editable( name ) == False ): return False
        print "module edit button clicked on:", name          
        module_window = ModuleWindow ( self )
        module_window.load( name )
        module_window.run()  
        self.refresh_config_test()
              
    def quit (self, widget):
        print 'quitting'
        gtk.main_quit()
        exit()
    
    def create_vhost_list(self ):
        #print parent
        #sw = gtk.ScrolledWindow()
        sw = self.xml.get_widget( 'vhosts_scroll_box' )      
        # create virtualhosts treeview
        treeview = VhostsTreeView.VhostsTreeView()
        treeview.selected_callback = self.row_selected
        treeview.connect_after("row-activated", self.edit_button_clicked )
        self.vhosts_treeview = treeview        
        self.xml.get_widget( 'vhost_container' ).add(treeview)        
        self.xml.get_widget( 'vhost_container' ).reorder_child( treeview, 0)

        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        
        # create denormalized vhosts.
        # We check for conf files only present in /etc/apache2/sites-enabled,
        # display them as a separate list and offer user to normalize them
        # moving them in /etc/apache2/sites-available and linking them back
        # from /etc/apache2/sites-enabled
        
        denormalized_treeview = VhostsTreeView.DenormalizedVhostsTreeView()
        self.denormalized_treeview = denormalized_treeview        
        #self.xml.get_widget( 'problems_area' ).add(denormalized_treeview)        
        #self.xml.get_widget( 'problems_area' ).reorder_child( denormalized_treeview, 2)
        denormalized_treeview.set_sensitive( False )
        denormalized_treeview.show()
        sw.show_all()
        #hidden by default
        #self.xml.get_widget( 'unnormalized_notice' ).hide_all()
        
    def create_errors_list(self):
        self.treeview_errors = VhostsTreeView.ErrorsTreeView()
        #treeview.selected_callback = self.row_selected
        #treeview.connect_after("row-activated", self.edit_button_clicked )
        #self.vhosts_treeview = treeview        
        
        self.xml.get_widget( 'viewport_errors' ).add(self.treeview_errors) 
        self.xml.get_widget( 'viewport_errors' ).show_all()
        
        #self.refresh_config_test()
    
    def create_modules_list(self ):
        sw = self.xml.get_widget( 'modules_scroll_box' )
        # create virtualhosts treeview
        treeview = VhostsTreeView.ModulesTreeView()
        treeview.connect_after("row-activated", self.edit_module_button_clicked )
        treeview.selected_callback = self.module_row_selected
        self.modules_treeview = treeview        
        self.xml.get_widget( 'modules_container' ).add(treeview)        
        self.xml.get_widget( 'modules_container' ).reorder_child( treeview, 0)
        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.show_all()
                      
    def refresh_vhosts ( self ):
        print "reloading vhosts.."            
        self.vhosts_treeview.load()
    def refresh_denormalized_vhosts (self):
        self.denormalized_treeview.load()
        #if ( len( self.denormalized_treeview.items ) > 0 ):
            #self.xml.get_widget( 'unnormalized_notice' ).show_all()
            #self.xml.get_widget( 'notebook' ).get_nth_page( 2 ).show()
        #else:
            #self.xml.get_widget( 'unnormalized_notice' ).hide_all()
            #self.xml.get_widget( 'notebook' ).get_nth_page( 2 ).hide()
    def refresh_modules (self):    
        print "reloading modules.."            
        self.modules_treeview.load()
    def refresh_lists (self):
        self.refresh_vhosts()
        self.refresh_modules()
        self.refresh_denormalized_vhosts()
        self.refresh_config_test()
    def please_restart ( self ):
        self.xml.get_widget( 'restart_apache_notice' ).show()
    def restart_apache ( self, widget ):
        print "Restarting apache on user's request"
        self.apache.restart()
        self.update_server_status()
        self.xml.get_widget( 'restart_apache_notice' ).hide()
        self.refresh_lists()
        self.refresh_config_test()
        
    def is_vhost_editable (self, name):
        return name != 'default'
    def is_module_editable (self, name):
        editable = False
        if name:
            mod = self.modules_treeview.items[ name+".load" ]
            editable = mod.data[ 'configurable' ]
        return editable
    def row_selected( self, widget ):
        name = self.vhosts_treeview.get_selected_line()
        if ( name == None ):
            self.xml.get_widget( 'delete_button' ).set_sensitive( False )
            self.xml.get_widget( 'edit_button' ).set_sensitive( False )
            self.xml.get_widget( 'surf_this_button' ).set_sensitive( False )
        else:
            editable = self.is_vhost_editable( name )
            self.xml.get_widget( 'delete_button' ).set_sensitive( editable )
            self.xml.get_widget( 'edit_button' ).set_sensitive( editable )
            surfable =  self.get_current_vhost().get_server_name() != None
            self.xml.get_widget( 'surf_this_button' ).set_sensitive( surfable )
            browsable =  self.get_current_vhost().config.DocumentRoot.value != None
            self.xml.get_widget( 'browse_button' ).set_sensitive( browsable )
    def module_row_selected( self, widget):
        name = self.modules_treeview.get_selected_line()
        editable = self.is_module_editable(name)
        self.xml.get_widget( 'edit_module_button' ).set_sensitive( editable )
        if name != None: self.xml.get_widget( 'open_doc_button' ).set_sensitive( True )
    # TODO: open doc only for apache2.2 own modules, not third-party (eg mod_php5)
    # TODO: sniff apache version, don't hardcode it
    def open_doc_button_clicked( self, widget ):
        name = self.modules_treeview.get_selected_line()
        if ( name == None ): return False
        open_module_doc(name)
        
    def fix_vhosts(self, widget):
        items = self.denormalized_treeview.get_items()
        for name in items:
            normalize_vhost( name )
        #since they were in the enabled, let's enabl'em again
        for name in items:
            site = VirtualHostModel( name )
            site.toggle(True)            
        self.refresh_vhosts()
        self.refresh_denormalized_vhosts()
    def get_current_vhost(self ):
        name = self.vhosts_treeview.get_selected_line()
        if ( name == None ): return None
        return self.vhosts_treeview.items[ name ]
    def surf_this(self, widget):
        name = self.vhosts_treeview.get_selected_line()
        if name == 'default':
            server_name = 'localhost'
        else:
            server_name = self.get_current_vhost().get_server_name()
            
        protocol = "http"    
        #FIXME: reimplement this when we have port methods again
        #if str(self.vhosts_treeview.items[ name ].get_value("port", "80")) == "443":
        #    protocol = "https"
            
        if ( server_name ): Desktop.open_url( protocol+"://" + server_name )
    def browse_this(self, widget):
        document_root = self.get_current_vhost().config.DocumentRoot.value
        Desktop.open_dir( document_root )
        

    def display_about (self, widget):
        dialog = gtk.AboutDialog()
        dialog.set_name( APPNAME )
        dialog.set_version( APPVERSION )
        dialog.set_authors( ["Rapache Developers\nhttps://launchpad.net/~rapache-devel"] )
        dialog.set_comments('Rapache is an Apache configurator for Ubuntu/Gnome systems')
        dialog.set_website('http://launchpad.net/rapache')
        dialog.run()
        dialog.destroy()
