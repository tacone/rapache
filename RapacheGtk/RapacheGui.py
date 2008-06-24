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
              
        #Set the Glade file
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
            "quit" : self.quit }
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
        VirtualHostWindow ( self )
        
    def edit_button_clicked(self, widget, notused = None, notused2 = None):        
        name = self.vhosts_treeview.get_selected_line()
        print "edit button clicked on:" + name          
        new_vhost_window = VirtualHostWindow ( self )
        new_vhost_window.load( name )
            
    def delete_button_clicked( self, widget ):
        name = self.vhosts_treeview.get_selected_line()
        if ( name == None ): return False
        result = easygui.message_box(
            title='Delete '+name,
            message="You are about to delete the following domain: \n\n"+name+"\n\nData won't be recoverable. Proceed ?",
            buttons=('Ok', 'Cancel'))
        if ( result != "Ok" ): return False
        site = VirtualHostModel( name )
        site.delete()
        self.vhosts_treeview.load()
        print "========================================"
        print "========================================"
        print "========================================"                
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
        self.xml.get_widget( 'vhost_container' ).add(denormalized_treeview)        
        self.xml.get_widget( 'vhost_container' ).reorder_child( denormalized_treeview, 2)
        denormalized_treeview.set_sensitive( False )
        denormalized_treeview.show()
        sw.show_all()
        #hidden by default
        self.xml.get_widget( 'unnormalized_notice' ).hide_all()
        

        
    
    def create_modules_list(self ):
        #print parent
        #sw = gtk.ScrolledWindow()
        sw = self.xml.get_widget( 'modules_scroll_box' )
        """
        try:
            try:
                self.modules_treeview.unregister()
            except:
                pass
            self.modules_treeview = None
            #self.modules_treeview.destroy()
        except:
            pass
        try:
            pass#self.denormalized_treeview.destroy()
        except:
            pass
        """
        
        # create virtualhosts treeview
        treeview = VhostsTreeView.ModulesTreeView()
        #treeview.load()        
        #treeview.selected_callback = self.row_selected
        #treeview.connect_after("row-activated", self.edit_button_clicked )
        self.modules_treeview = treeview        
        self.xml.get_widget( 'modules_container' ).add(treeview)        
        self.xml.get_widget( 'modules_container' ).reorder_child( treeview, 0)

        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        
        # create denormalized module list.
        # We check for conf files only present in /etc/apache2/mods-enabled,
        # display them as a separate list and offer user to normalize them
        # moving them in /etc/apache2/mods-available and linking them back
        # from /etc/apache2/mods-enabled
        """
        denormalized_treeview = VhostsTreeView.DenormalizedVhostsTreeView()
        denormalized_treeview.load()
        if ( denormalized_treeview.is_empty() == False ):           
            self.denormalized_treeview = denormalized_treeview        
            self.xml.get_widget( 'vhost_container' ).add(denormalized_treeview)        
            self.xml.get_widget( 'vhost_container' ).reorder_child( denormalized_treeview, 2)
            denormalized_treeview.set_sensitive( False )
            denormalized_treeview.show()
            sw.show_all()
        else:
            sw.show_all()
            self.xml.get_widget( 'unnormalized_notice' ).hide_all()
        """
        sw.show_all()
          
    def _change_label ( self, button, new_label ):
        """Changes the label of a button"""
        button.show()
        alignment = button.get_children()[0]
        hbox = alignment.get_children()[0]
        image, label = hbox.get_children()
        label.set_text( new_label )
        

    """def load_denormalized_vhosts(self):
        self.denormalized_virtual_hosts = {}
        site_template = "<b><big>%s</big></b>"        
        lstore = gtk.ListStore(
            gobject.TYPE_BOOLEAN,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING)
        data = []  
        dirList=os.listdir( Configuration.SITES_ENABLED_DIR )
        dirList = [x for x in dirList if self._blacklisted( x ) == False ]
        dirList = [x for x in dirList if is_denormalized_vhost( x ) == False ]
                   
        for fname in  dirList :
            site = VirtualHostModel( fname )                        
            self.denormalized_virtual_hosts[ fname ] = site
            site = None

        for idx in sorted( self.denormalized_virtual_hosts ):            
            site = self.denormalized_virtual_hosts[ idx ]
            normalizable = not is_not_normalizable(site.data['name'])
            markup = site_template % site.data['name']
            if ( normalizable == False ):
                markup = markup + " CANNOT FIX"
            iter = lstore.append()
            lstore.set(iter,
                COLUMN_FIXED, normalizable,
                COLUMN_SEVERITY, site.data['name'],
                COLUMN_MARKUP, markup 
                )
        return lstore"""
            
    def refresh_vhosts ( self ):
        print "reloading vhosts.."            
        self.vhosts_treeview.load()
    def refresh_denormalized_vhosts (self):
        self.denormalized_treeview.load()
        if ( len( self.denormalized_treeview.items ) > 0 ):
            self.xml.get_widget( 'unnormalized_notice' ).show_all()
        else:
            self.xml.get_widget( 'unnormalized_notice' ).hide_all()
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
        else:
            self.xml.get_widget( 'delete_button' ).set_sensitive( True )
            self.xml.get_widget( 'edit_button' ).set_sensitive( True )
                
    """def __add_denormalized_columns(self, treeview):
        model = treeview.get_model()
       
        column = gtk.TreeViewColumn()
        cellRenderer = gtk.CellRendererPixbuf()
        cellRenderer.set_property( 'stock-id',  gtk.STOCK_DIALOG_WARNING )
        column.pack_start(cellRenderer, expand = False)
        treeview.append_column(column)           
        # column for description
        column = gtk.TreeViewColumn('Description', gtk.CellRendererText(),
                                     markup=COLUMN_MARKUP)
        column.set_sort_column_id(COLUMN_MARKUP)
        treeview.append_column(column)               
    """    
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
