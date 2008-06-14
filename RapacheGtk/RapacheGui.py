#!/usr/bin/env python
#
# Copyright (C) Stefano Forenza 2008 <tacone@gmail.com>
# 
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# main.py is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


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
from RapacheCore.VirtualHost import VirtualHostModel
from RapacheGtk import easygui

data = \
[(False, "Loading", "please wait" )]

APPNAME="Rapache"
APPVERSION="0.1"


class MainWindow:
    """This is an Hello World GTK application"""

    def __init__(self, Configuration):

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
            "quit" : self.quit }
        self.xml.signal_autoconnect(dic)
        self._change_label ( self.xml.get_widget( 'restart_apache' ), "Restart\nApache" )
        self.create_vhost_list()
        self.new_vhost_window = None
    
    def browse_sites_available(self, widget):
        self.command ('gksudo "nautilus '+self.Configuration.SITES_AVAILABLE_DIR+' --no-desktop" & ' )
        return
    def get_selected_vhost( self ):
        try:
            selection = self.vhosts_list.get_selection()
            rows = selection.get_selected_rows()[1][0]
            num_row = rows[0]
            model = self.vhosts_list.get_model()
            name = model[ num_row ][1]
            return name
        except:
            return None
        
    def new_button_clicked(self, widget):
        if ( self.new_vhost_window ):
            print "A window is already open"
            print self.new_vhost_window
            return
        self.new_vhost_window = VirtualHostWindow ( self.Configuration.GLADEPATH, self )
        
    def edit_button_clicked(self, widget):        
        name = self.get_selected_vhost()
        print "edit button clicked on:" + name

        if ( self.new_vhost_window ):
            print "A window is already open"
            print self.new_vhost_window
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
        sw = self.xml.get_widget( 'vhost_container' )
        try:
            self.vhosts_list.destroy()
        except:
            1
            
        self.xml.get_widget( 'vhost_container' )
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        # create tree model
        model = self.load_vhosts()

        # create tree view
        treeview = gtk.TreeView(model)
        treeview.set_headers_visible( False )
        treeview.set_rules_hint(True)
        treeview.set_search_column(COLUMN_SEVERITY)
        self.vhosts_list = treeview
        sw.add(treeview)
        
        # add columns to the tree view
        self.__add_columns(treeview)

        sw.show_all()
        
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
        if re.match( '.*[~]$', fname ) != None : return False
        if re.match( '.*.swp$', fname ) != None : return False
        return True
    def load_vhosts(self):
        lstore = gtk.ListStore(
            gobject.TYPE_BOOLEAN,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING)
        data = []  
        dirList=os.listdir( self.Configuration.SITES_AVAILABLE_DIR )
        #blacklist

        for idx, fname in enumerate( dirList ):
            if self._blacklisted( fname ) == False : del dirList[ idx ]
            
        for fname in sorted( dirList ):
            isLink = self.is_site_enabled( fname )
            data.append( ( isLink, fname, 'normal' ) )           

        for item in data:
            iter = lstore.append()
            lstore.set(iter,
                COLUMN_FIXED, item[COLUMN_FIXED],
                COLUMN_SEVERITY, item[COLUMN_SEVERITY],
                COLUMN_MARKUP, "<b><big>%s</big></b>\n<small>DocumentRoot: /var/www/htdocs/example</small>"
                % ( item[COLUMN_SEVERITY]) )    
        return lstore
        
    def reload_vhosts ( self ):
        print "reloading vhosts.."
        #recreate model
        model = self.load_vhosts()            
        self.vhosts_list.set_model ( model )
        
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
        print site.data
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
        #stock = model.get_value(iter, 4)
        #print stock
        
        #Stock icon sizes are gtk.ICON_SIZE_MENU, gtk.ICON_SIZE_SMALL_TOOLBAR, 
        #gtk.ICON_SIZE_LARGE_TOOLBAR, gtk.ICON_SIZE_BUTTON, gtk.ICON_SIZE_DND 
        #and gtk.ICON_SIZE_DIALOG
        
        #/usr/share/icons/Human/48x48/filesystems/gnome-fs-web.png
        #pixbuf = self.vhosts_list.render_icon(gtk.STOCK_NO , gtk.ICON_SIZE_LARGE_TOOLBAR, None)
        
        #TODO CHANGE THIS !
        filename = model.get_value(iter, COLUMN_SEVERITY )
        filename = '/var/www/%s/httpdocs/favicon.ico' % filename
        
        if ( os.path.exists( filename ) == False ): 
            filename = '/usr/share/icons/Human/24x24/filesystems/gnome-fs-web.png'
        pixbuf = gtk.gdk.pixbuf_new_from_file( filename )
        cell.set_property("pixbuf", pixbuf)

         
    def __add_columns(self, treeview):
        #print os.system( 'ls' )
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
        
        """
        # columns for severities
        column = gtk.TreeViewColumn('Vhost Name', gtk.CellRendererText(), text    =COLUMN_SEVERITY)
        column.set_sort_column_id(COLUMN_SEVERITY)
        treeview.append_column(column)
        """
        # column for description
        column = gtk.TreeViewColumn('Description', gtk.CellRendererText(),
                                     markup=COLUMN_MARKUP)
        column.set_sort_column_id(COLUMN_MARKUP)
        treeview.append_column(column)
               
        treeview.get_selection().connect("changed", self.row_selected )

  

