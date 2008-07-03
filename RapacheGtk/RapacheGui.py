#!/usr/bin/env python

#TODO throw appropriate exceptions (bug: vhost already exist displays only 
# after actually trying to create it's dir. check before )

#TODO read ERRORLEVEL from command line operations
#TODO stop operation if gksudo fails
#TODO check for sites-enabled-only sites and normalize them

#TODO delete-tarantella: hosts deletion & confirmation

#TODO refuse to edit complex vhosts ( done ? )

import gnome.ui
import gobject
import gtk
import os
import re
(
    COLUMN_FIXED,
    COLUMN_SEVERITY,
    COLUMN_MARKUP
) = range(3)


from RapacheGtk.VirtualHostGui import VirtualHostWindow
from RapacheCore.VirtualHost import *
from RapacheGtk import easygui
from RapacheGtk import GuiUtils
from RapacheCore import Shell
import VhostsTreeView
import RapacheCore.Observer
from RapacheGtk.EventDispatcher import Master
import subprocess

data = \
[(False, "Loading", "please wait" )]

APPNAME="Rapache"
APPVERSION="0.1"


class MainWindow( RapacheCore.Observer.Observable ) :
    """This is an Hello World Rapacheefication application"""
    
    def __init__(self, *args, **kwargs):
        super (MainWindow, self).__init__ (*args, **kwargs)
        Master.register(self)

        self.denormalized_virtual_hosts = {}
        gnome.init(APPNAME, APPVERSION)
        self.gladefile = Configuration.GLADEPATH + "/" + "main.glade"  
        self.xml = gtk.glade.XML(self.gladefile)         
        #Create our dictionary and connect it
        dic = { "new_button_clicked" : self.new_button_clicked,
            "on_MainWindow_destroy" : self.quit ,
            "please_restart" : self.restart_apache ,            
            "on_delete" : self.delete_button_clicked,
            "edit_button_clicked" : self.edit_button_clicked,
            "browse_sites_available" : self.browse_sites_available,
            "fix_vhosts_clicked" : self.fix_vhosts,
            "surf_this_button_clicked" : self.surf_this,
            "browse_button_clicked" : self.browse_this,
            "quit" : self.quit }
        gtk.window_set_default_icon(self.xml.get_widget("MainWindow").get_icon())
        self.xml.signal_autoconnect(dic)
        self._change_label ( self.xml.get_widget( 'restart_apache' ), "Restart\nApache" )
        self._change_label ( self.xml.get_widget( 'fix_vhosts' ), "Fix Virtual Hosts" )
        #hereby we create lists
        self.create_vhost_list()
        self.create_modules_list()
        #hereby we fill them
        self.refresh_lists()
        
        GuiUtils.style_as_tooltip( self.xml.get_widget( 'restart_apache_notice' ) )
        GuiUtils.style_as_tooltip( self.xml.get_widget( 'unnormalized_notice' ) )    
        
    def handle_event(self, event ):
        if event.name == 'please_restart_apache':
            self.please_restart()
            return
        if event.name == 'please_reload_lists':
            self.load_lists()
            return
    def browse_sites_available(self, widget):
        Shell.command ('gksudo "nautilus '+Configuration.SITES_AVAILABLE_DIR+' --no-desktop" & ' )
        return
    
    def new_button_clicked(self, widget):
        new_vhost_window = VirtualHostWindow ( self )
        #new_vhost_window.load()
        new_vhost_window.run()
    def edit_button_clicked(self, widget, notused = None, notused2 = None):        
        name = self.vhosts_treeview.get_selected_line()
        print "edit button clicked on:" + name          
        new_vhost_window = VirtualHostWindow ( self )
        new_vhost_window.load( name )
        new_vhost_window.run()    
    def delete_button_clicked( self, widget ):
        name = self.vhosts_treeview.get_selected_line()
        if ( name == None ): return False
        result = easygui.message_box(
            title='Delete '+name,
            message="You are about to delete the following domain: \n\n"+name+"\n\nData won't be recoverable. Proceed ?",
            surf_thisbuttons=('Ok', 'Cancel'))
        if ( result != "Ok" ): return False
        site = VirtualHostModel( name )
        site.delete()
        self.vhosts_treeview.load()
        self.please_restart()
        
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
        self.xml.get_widget( 'problems_area' ).add(denormalized_treeview)        
        self.xml.get_widget( 'problems_area' ).reorder_child( denormalized_treeview, 2)
        denormalized_treeview.set_sensitive( False )
        denormalized_treeview.show()
        sw.show_all()
        #hidden by default
        self.xml.get_widget( 'unnormalized_notice' ).hide_all()
    
    def create_modules_list(self ):
        sw = self.xml.get_widget( 'modules_scroll_box' )
        # create virtualhosts treeview
        treeview = VhostsTreeView.ModulesTreeView()
        self.modules_treeview = treeview        
        self.xml.get_widget( 'modules_container' ).add(treeview)        
        self.xml.get_widget( 'modules_container' ).reorder_child( treeview, 0)
        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.show_all()
          
    def _change_label ( self, button, new_label ):
        """Changes the label of a button"""
        button.show()
        alignment = button.get_children()[0]
        hbox = alignment.get_children()[0]
        image, label = hbox.get_children()
        label.set_text( new_label )
            
    def refresh_vhosts ( self ):
        print "reloading vhosts.."            
        self.vhosts_treeview.load()
    def refresh_denormalized_vhosts (self):
        self.denormalized_treeview.load()
        if ( len( self.denormalized_treeview.items ) > 0 ):
            self.xml.get_widget( 'unnormalized_notice' ).show_all()
            self.xml.get_widget( 'notebook' ).get_nth_page( 2 ).show()
        else:
            self.xml.get_widget( 'unnormalized_notice' ).hide_all()
            self.xml.get_widget( 'notebook' ).get_nth_page( 2 ).hide()
    def refresh_modules (self):    
        print "reloading modules.."            
        self.modules_treeview.load()
    def refresh_lists (self):
        self.refresh_vhosts()
        self.refresh_modules()
        self.refresh_denormalized_vhosts()
    def please_restart ( self ):
        self.xml.get_widget( 'restart_apache_notice' ).show()
    def restart_apache ( self, widget ):
        print "Restarting apache on user's request"
        Shell.command( "gksudo /etc/init.d/apache2 stop" )
        Shell.command( "gksudo /etc/init.d/apache2 start" )
        self.xml.get_widget( 'restart_apache_notice' ).hide()
        self.refresh_lists()
    def row_selected( self, widget ):
        name = self.vhosts_treeview.get_selected_line()
        if ( name == None ):
            self.xml.get_widget( 'delete_button' ).set_sensitive( False )
            self.xml.get_widget( 'edit_button' ).set_sensitive( False )
            self.xml.get_widget( 'open_in_browser_button' ).set_sensitive( False )
        else:
            self.xml.get_widget( 'delete_button' ).set_sensitive( True )
            self.xml.get_widget( 'edit_button' ).set_sensitive( True )
            surfable =  self.get_current_vhost_directive( 'domain_name' ) != None
            self.xml.get_widget( 'surf_this_button' ).set_sensitive( surfable )
            browsable =  self.get_current_vhost_directive( 'target_folder' ) != None
            self.xml.get_widget( 'browse_button' ).set_sensitive( browsable )
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
    def get_current_vhost_directive (self, directive_name ):
        name = self.vhosts_treeview.get_selected_line()
        if ( name == None ): return None
        return self.vhosts_treeview.items[ name ].data[ directive_name ]
    def surf_this(self, widget):
        server_name = self.get_current_vhost_directive( 'domain_name' )
        if ( server_name ): self.open_url( "http://" + server_name )
    def browse_this(self, widget):
        document_root = self.get_current_vhost_directive( 'target_folder' )
        Shell.command ('gksudo "nautilus '+document_root+' --no-desktop" & ' )
        
        if ( server_name ): self.open_url( "http://" + server_name )
    # Grabbed from Ubuntu's UpdateManager (ChangelogViewer.py)    
    #  Copyright (c) 2006 Sebastian Heinlein
    #                2007 Canonical    
    # TODO: move this into an utility module
    def open_url(self, url):
        """Open the specified URL in a browser"""
        # Find an appropiate browser
        if os.path.exists('/usr/bin/gnome-open'):
            command = ['gnome-open', url]
        else:
            command = ['x-www-browser', url]

        # Avoid to run the browser as user root
        if os.getuid() == 0 and os.environ.has_key('SUDO_USER'):
            command = ['sudo', '-u', os.environ['SUDO_USER']] + command

        subprocess.Popen(command)
