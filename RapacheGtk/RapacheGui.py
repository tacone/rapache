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
        self.create_vhost_list()
        self.new_vhost_window = None
        GuiUtils.style_as_tooltip( self.xml.get_widget( 'restart_apache_notice' ) )
        GuiUtils.style_as_tooltip( self.xml.get_widget( 'unnormalized_notice' ) )    
    
    def handle_event(self, event ):
        if event.name == 'please_restart_apache':
            self.please_restart()
    def browse_sites_available(self, widget):
        Shell.command ('gksudo "nautilus '+Configuration.SITES_AVAILABLE_DIR+' --no-desktop" & ' )
        return
    
    def new_button_clicked(self, widget):
        if ( self.new_vhost_window ):
            print "A window is already open"
            return
        self.new_vhost_window = VirtualHostWindow ( self )
        
    def edit_button_clicked(self, widget, notused = None, notused2 = None):        
        name = self.vhosts_treeview.get_selected_line()
        print "edit button clicked on:" + name
        if ( self.new_vhost_window ):
            print "A window is already open"
            return
        
        self.new_vhost_window = VirtualHostWindow ( self )
        self.new_vhost_window.load( name )
            
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
        self.create_vhost_list()
        self.please_restart()
        
    def quit (self, widget):
        print 'quitting'
        gtk.main_quit()
        exit()
        
    def create_vhost_list(self ):
        #print parent
        #sw = gtk.ScrolledWindow()
        sw = self.xml.get_widget( 'scroll_box' )
        try:
            self.vhosts_treeview.destroy()
        except:
            pass
        try:
            self.denormalized_treeview.destroy()
        except:
            pass
        
        # create tree view
        treeview = VhostsTreeView.VhostsTreeView()
        treeview.load()        
        treeview.selected_callback = self.row_selected
        treeview.connect_after("row-activated", self.edit_button_clicked )
        
        self.vhosts_treeview = treeview        
        # attach it
        self.xml.get_widget( 'vhost_container' ).add(treeview)        
        self.xml.get_widget( 'vhost_container' ).reorder_child( treeview, 0)

        sw.set_shadow_type(gtk.SHADOW_NONE)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        
        # create denormalized vhosts.
        # We check for conf files only present in /etc/apache2/sites-enabled,
        # display them as a separate list and offer user to normalize them
        # moving them in /etc/apache2/sites-available and linking them back
        # from /etc/apache2/sites-enabled
        
        """denormalized_treeview = VhostsTreeView.VhostsTreeView()
        denormalized_treeview.load() 
        self.xml.get_widget( 'vhost_container' ).add(denormalized_treeview) 
        self.xml.get_widget( 'unnormalized_notice' ).show_all()
        
        self.xml.get_widget( 'vhost_container' ).reorder_child( denormalized_treeview, 2)
        """
        denormalized_model = self.load_denormalized_vhosts()
        if len( self.denormalized_virtual_hosts ) > 0 :
            self.xml.get_widget( 'unnormalized_notice' ).show_all()
            denormalized_treeview = gtk.TreeView(denormalized_model)
            denormalized_treeview.set_headers_visible( False )
            denormalized_treeview.set_rules_hint(True)
            self.__add_denormalized_columns(denormalized_treeview)
            denormalized_treeview.set_sensitive( False )
            denormalized_treeview.show()
            self.denormalized_treeview = denormalized_treeview
            # attach it
            self.xml.get_widget( 'vhost_container' ).add(denormalized_treeview)        
            self.xml.get_widget( 'vhost_container' ).reorder_child( denormalized_treeview, 2)
            sw.show_all()
        else:
            sw.show_all()
            self.xml.get_widget( 'unnormalized_notice' ).hide_all()
            
    def _blacklisted ( self, fname ):
        if re.match( '.*[~]\s*$', fname ) != None : return True
        if re.match( '.*.swp$', fname ) != None : return True
        return False
    def _change_label ( self, button, new_label ):
        """Changes the label of a button"""
        button.show()
        alignment = button.get_children()[0]
        hbox = alignment.get_children()[0]
        image, label = hbox.get_children()
        label.set_text( new_label )
        

    def load_denormalized_vhosts(self):
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
        return lstore
            
    def reload_vhosts ( self ):
        print "reloading vhosts.."
        #recreate model
        model = self.load_vhosts()            
        self.vhosts_treeview.set_model ( model )
        
    
               
    def please_restart ( self ):
        self.xml.get_widget( 'restart_apache_notice' ).show()
   
    
    def restart_apache ( self, widget ):
        print "Restarting apache on user's request"
        Shell.command( "gksudo /etc/init.d/apache2 stop" )
        Shell.command( "gksudo /etc/init.d/apache2 start" )
        self.xml.get_widget( 'restart_apache_notice' ).hide()
    def row_selected( self, widget ):
        name = self.vhosts_treeview.get_selected_line()
        if ( name == None ):
            self.xml.get_widget( 'delete_button' ).set_sensitive( False )
            self.xml.get_widget( 'edit_button' ).set_sensitive( False )
        else:
            self.xml.get_widget( 'delete_button' ).set_sensitive( True )
            self.xml.get_widget( 'edit_button' ).set_sensitive( True )
    
    def __add_denormalized_columns(self, treeview):
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
        
    def fix_vhosts(self, widget):
        for name in self.denormalized_virtual_hosts:
            normalize_vhost( name )
        #since they were in the enabled, let's enabl'em again
        for name in self.denormalized_virtual_hosts:
            site = VirtualHostModel( name )
            site.toggle(True)            
        self.create_vhost_list()
