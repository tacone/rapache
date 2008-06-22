import gtk
import gobject
from CheckListView import *
import os
import re
from RapacheCore.VirtualHost import *
from RapacheCore import Configuration

class ConfFilesTreeView( CheckListView ):
    def __init__ (self, *args, **kwargs):
        super (ConfFilesTreeView, self).__init__ (*args, **kwargs)
        self.items = {}
    def _blacklisted ( self, fname ):
        if re.match( '.*[~]\s*$', fname ) != None : return True
        if re.match( '.*.swp$', fname ) != None : return True
        return False 
    def is_empty (self):
        return len( self.items ) == 0
    def get_items(self):
        return self.items
gobject.type_register (ConfFilesTreeView)


class VhostsTreeView ( ConfFilesTreeView ):
    def __init__ (self, *args, **kwargs):
        super (VhostsTreeView, self).__init__ (*args, **kwargs)
        self.icon_callback = self.__get_row_icon  
        self.toggled_callback = self.__fixed_toggled
            
    def load(self):
        self.items = {}
        site_template = "<b><big>%s</big></b>\n<small>DocumentRoot: %s</small>"
        site_unparsable_template = "<b><big>%s</big></b>\n<small><i>Further information not available</i></small>"
        lstore = gtk.ListStore(
            gobject.TYPE_BOOLEAN,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING)
        data = []  

        dirList=os.listdir( Configuration.SITES_AVAILABLE_DIR )
        dirList = [x for x in dirList if self._blacklisted( x ) == False ]            
        for fname in  dirList :                        
            site = VirtualHostModel( fname )
            try:
                site.load()
            except "VhostUnparsable":
                pass
            self.items[ fname ] = site
            site = None
                            
        for idx in sorted( self.items ):
            site = self.items[ idx ]
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
            
        self._post_load(lstore)
        
        

     #TODO: warning ! This function get's called even on mousehover
    #      check for a way to optimize it
    def __get_row_icon (self, column, cell, model, iter):
        """ Provides the icon for a virtual host looking up it's favicon"""        
        """node = model.get_value(iter, MODEL_FIELD_NODE)
        pixbuf = getPixbufForNode(node)
        cell.set_property('pixbuf', pixbuf)"""                
        favicon = '/usr/share/icons/Human/24x24/filesystems/gnome-fs-web.png'
        fname = model.get_value(iter, COLUMN_SEVERITY )
        site = self.items[ fname ]
        if site.data['target_folder'] != None:
            custom_favicon = os.path.join(os.path.dirname( site.data['target_folder']+"/" ), "favicon.ico")                                                    
            if ( os.path.exists( custom_favicon ) ): favicon = custom_favicon
            
        pixbuf = gtk.gdk.pixbuf_new_from_file( favicon )
        cell.set_property("pixbuf", pixbuf)
        
    def __fixed_toggled(self, cell, path, treeview):        
        # get toggled iter        
        model = treeview.get_model()
        iter = model.get_iter((int(path),))
        fixed = model.get_value(iter, COLUMN_FIXED)
        name = model.get_value(iter, COLUMN_SEVERITY)
        
        fixed = not fixed        
        if fixed:
            Shell.command ('gksudo '+Configuration.APPPATH+'"/hosts-manager -a '+name+'"')
        else :
            Shell.command ('gksudo '+Configuration.APPPATH+'"/hosts-manager -r '+name+'"')
        # set new value        
        site = VirtualHostModel( name )
        site.toggle( fixed )
        model.set(iter, COLUMN_FIXED, site.data['enabled'] )        
        if ( site.changed ):
            #self.please_restart()
            self.raise_event( 'please_restart_apache' )                
gobject.type_register (VhostsTreeView)

class DenormalizedVhostsTreeView ( ConfFilesTreeView ):
    def __init__ (self, *args, **kwargs):
        super (DenormalizedVhostsTreeView, self).__init__ (*args, **kwargs)
        print self.column_checkbox, self.column_description, self.column_icon
        self.column_checkbox.set_visible( False )
        print self.column_icon.get_cell_renderers()[0].set_property( 'stock-id',  gtk.STOCK_DIALOG_WARNING )
    def load(self):    
        self.items = {}
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
            self.items[ fname ] = site
            site = None

        for idx in sorted( self.items ):            
            site = self.items[ idx ]
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
        self._post_load(lstore)
    def toggled_callback(self, *args, **kwargs):
        pass
gobject.type_register (DenormalizedVhostsTreeView )

