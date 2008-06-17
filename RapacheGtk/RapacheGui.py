#!/usr/bin/env python


#TODO Refactor CRUD in VirtualHost class

#TODO move configs into a separate module

#TODO throw appropriate exceptions (bug: vhost already exist doesn't display)

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
data = \
[(False, "Loading", "please wait" )]

APPNAME="Rapache"
APPVERSION="0.1"


class MainWindow:
    """This is an Hello World Rapacheefication application"""
    
    def __init__(self, Configuration):
        self.virtual_hosts = {}
        self.denormalized_virtual_hosts = {}
        gnome.init(APPNAME, APPVERSION)
        
        self.Configuration = Configuration 
        
        #Set the Glade file
        self.gladefile = self.Configuration.GLADEPATH + "/" + "main.glade"  
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
    def browse_sites_available(self, widget):
        self.command ('gksudo "nautilus '+self.Configuration.SITES_AVAILABLE_DIR+' --no-desktop" & ' )
        return
    def get_selected_vhost( self ):
        try:
            selection = self.vhosts_treeview.get_selection()
            rows = selection.get_selected_rows()[1][0]
            num_row = rows[0]
            model = self.vhosts_treeview.get_model()
            name = model[ num_row ][1]
            return name
        except:
            return None
        
    def new_button_clicked(self, widget):
        if ( self.new_vhost_window ):
            print "A window is already open"
            return
        self.new_vhost_window = VirtualHostWindow ( self.Configuration.GLADEPATH, self )
        
    def edit_button_clicked(self, widget):        
        name = self.get_selected_vhost()
        print "edit button clicked on:" + name
        if ( self.new_vhost_window ):
            print "A window is already open"
            return
        
        self.new_vhost_window = VirtualHostWindow ( self.Configuration.GLADEPATH, self )
        self.new_vhost_window.load( name )
            
    def delete_button_clicked( self, widget ):
        name = self.get_selected_vhost()
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
        model = self.load_vhosts()
        treeview = gtk.TreeView(model)
        treeview.set_headers_visible( False )
        treeview.set_rules_hint(True)
        treeview.set_search_column(COLUMN_SEVERITY)
        self.__add_columns(treeview)
        self.vhosts_treeview = treeview        
        # attach it
        self.xml.get_widget( 'vhost_container' ).add(treeview)        
        self.xml.get_widget( 'vhost_container' ).reorder_child( treeview, 0)

        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        
        # create denormalized vhosts
        
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
            
        
        

        

        
        # add columns to the tree view
        

        
        
    def _change_label ( self, button, new_label ):        
        button.show()
        alignment = button.get_children()[0]
        hbox = alignment.get_children()[0]
        image, label = hbox.get_children()
        label.set_text( new_label )
        
    def is_site_enabled ( self, orig ):
        dirList=os.listdir( self.Configuration.SITES_ENABLED_DIR )
        for fname in dirList:
            try:                
                flink = os.readlink( self.Configuration.SITES_ENABLED_DIR+"/"+fname )
                flink = os.path.join(os.path.dirname( self.Configuration.SITES_ENABLED_DIR ), flink)             
                if ( flink == self.Configuration.SITES_AVAILABLE_DIR+"/"+orig ):
                    return True
            except:
                1
        return False
    def _blacklisted ( self, fname ):
        if re.match( '.*[~]\s*$', fname ) != None : return True
        if re.match( '.*.swp$', fname ) != None : return True
        return False
    def load_vhosts(self):
        self.virtual_hosts = {}
        site_template = "<b><big>%s</big></b>\n<small>DocumentRoot: %s</small>"
        site_unparsable_template = "<b><big>%s</big></b>\n<small><i>Further information not available</i></small>"
        lstore = gtk.ListStore(
            gobject.TYPE_BOOLEAN,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING)
        data = []  
        dirList=os.listdir( self.Configuration.SITES_AVAILABLE_DIR )
        dirList = [x for x in dirList if self._blacklisted( x ) == False ]            
        for fname in  dirList :                        
            site = VirtualHostModel( fname )
            try:
                site.load()
            except "VhostUnparsable":
                pass
            self.virtual_hosts[ fname ] = site
            site = None

                            
        for idx in sorted( self.virtual_hosts ):
            
            site = self.virtual_hosts[ idx ]
            if ( site.parsable ):
                markup = site_template \
                % ( site.data['name'] , site.data[ 'target_folder' ] )
            else:
                markup = site_unparsable_template % site.data['name']
            iter = lstore.append()
            lstore.set(iter,
                COLUMN_FIXED, site.data['enabled'],
                COLUMN_SEVERITY, site.data['name'],
                COLUMN_MARKUP, markup )
             
        return lstore
    def load_denormalized_vhosts(self):
        self.denormalized_virtual_hosts = {}
        site_template = "<b><big>%s</big></b>"        
        lstore = gtk.ListStore(
            gobject.TYPE_BOOLEAN,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING)
        data = []  
        dirList=os.listdir( self.Configuration.SITES_ENABLED_DIR )
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
        
    def fixed_toggled(self, cell, path, model):
        simulation = True
        # get toggled iter
        iter = model.get_iter((int(path),))
        fixed = model.get_value(iter, COLUMN_FIXED)
        name = model.get_value(iter, COLUMN_SEVERITY)
        
        fixed = not fixed        
        if fixed:
    	    self.command ('gksudo '+self.Configuration.APPPATH+'"/hosts-manager.py -a '+name+'"')
        else :
    	    self.command ('gksudo '+self.Configuration.APPPATH+'"/hosts-manager.py -r '+name+'"')
        # set new value        
        site = VirtualHostModel( name )
        site.toggle( fixed )
        model.set(iter, COLUMN_FIXED, site.data['enabled'] )        
        if ( site.changed ):
            self.please_restart()
               
    def please_restart ( self ):
        self.xml.get_widget( 'restart_apache_notice' ).show()
    def command ( self, command ):
        print "COMMAND: "+command
        return os.system( command )
    def restart_apache ( self, widget ):
        print "Restarting apache on user's request"
        self.command( "gksudo /etc/init.d/apache2 stop" )
        self.command( "gksudo /etc/init.d/apache2 start" )
        self.xml.get_widget( 'restart_apache_notice' ).hide()
    def row_selected( self, widget ):
        name = self.get_selected_vhost()
        if ( name == None ):
            self.xml.get_widget( 'delete_button' ).set_sensitive( False )
            self.xml.get_widget( 'edit_button' ).set_sensitive( False )
        else:
            self.xml.get_widget( 'delete_button' ).set_sensitive( True )
            self.xml.get_widget( 'edit_button' ).set_sensitive( True )
    
    #TODO: warning ! This function get's called even on mousehover
    #      check for a way to optimize it
    def _get_vhost_icon (self, column, cell, model, iter):
        """node = model.get_value(iter, MODEL_FIELD_NODE)
        pixbuf = getPixbufForNode(node)
        cell.set_property('pixbuf', pixbuf)"""
                
        filename = model.get_value(iter, COLUMN_SEVERITY )
        site = self.virtual_hosts[ filename ]
        filename = os.path.join(os.path.dirname( site.data['target_folder']+"/" ), "favicon.ico")                        
        
        if ( os.path.exists( filename ) == False ): 
            filename = '/usr/share/icons/Human/24x24/filesystems/gnome-fs-web.png'
        pixbuf = gtk.gdk.pixbuf_new_from_file( filename )
        cell.set_property("pixbuf", pixbuf)

         
    def __add_columns(self, treeview):
        model = treeview.get_model()

        # column for fixed toggles
        renderer = gtk.CellRendererToggle()
        renderer.connect('toggled', self.fixed_toggled, model)
        
        column = gtk.TreeViewColumn('Enabled', renderer, active=COLUMN_FIXED)

        # set this column to a fixed sizing(of 50 pixels)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(40)
        treeview.append_column(column)

        column = gtk.TreeViewColumn()
        cellRenderer = gtk.CellRendererPixbuf()
        column.pack_start(cellRenderer, expand = False)
        column.set_cell_data_func(cellRenderer, self._get_vhost_icon)
        treeview.append_column(column)        
   
        # column for description
        column = gtk.TreeViewColumn('Description', gtk.CellRendererText(),
                                     markup=COLUMN_MARKUP)
        column.set_sort_column_id(COLUMN_MARKUP)
        treeview.append_column(column)
               
        treeview.get_selection().connect("changed", self.row_selected )

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
               
               
        treeview.get_selection().connect("changed", self.row_selected )
    def fix_vhosts(self, widget):
        for name in self.denormalized_virtual_hosts:
            normalize_vhost( name )
        #since they were in the enabled, let's enabl'em again
        for name in self.denormalized_virtual_hosts:
            site = VirtualHostModel( name )
            site.toggle(True)            
        self.create_vhost_list()
