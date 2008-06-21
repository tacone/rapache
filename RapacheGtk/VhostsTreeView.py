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
    def _blacklisted ( self, fname ):
        if re.match( '.*[~]\s*$', fname ) != None : return True
        if re.match( '.*.swp$', fname ) != None : return True
        return False 
gobject.type_register (ConfFilesTreeView)

class VhostsTreeView ( ConfFilesTreeView ):
    
    def __init__ (self, *args, **kwargs):
        super (VhostsTreeView, self).__init__ (*args, **kwargs)
        self.virtual_hosts = {}
        self.icon_callback = self.__get_row_icon  
        self.toggled_callback = self.fixed_toggled
    #----decorating observer    
    def register (self, *args, **kwargs): return self.Observable.register(*args, **kwargs)
    def unregister (self, *args, **kwargs): return self.Observable.unregister(*args, **kwargs)
    def handle_event (self, *args, **kwargs): return self.Observable.handle_event(*args, **kwargs)
    def raise_event (self, *args, **kwargs): return self.Observable.raise_event(*args, **kwargs)
    
    
    def load (self):
        model = self.load_vhosts()
        self.set_model( model )        
    def load_vhosts(self):
        self.virtual_hosts = {}
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
     #TODO: warning ! This function get's called even on mousehover
    #      check for a way to optimize it
    def __get_row_icon (self, column, cell, model, iter):
        """ Provides the icon for a virtual host looking up it's favicon"""
        
        """node = model.get_value(iter, MODEL_FIELD_NODE)
        pixbuf = getPixbufForNode(node)
        cell.set_property('pixbuf', pixbuf)"""
                
        favicon = '/usr/share/icons/Human/24x24/filesystems/gnome-fs-web.png'
        fname = model.get_value(iter, COLUMN_SEVERITY )
        site = self.virtual_hosts[ fname ]
        if site.data['target_folder'] != None:
            custom_favicon = os.path.join(os.path.dirname( site.data['target_folder']+"/" ), "favicon.ico")                                                    
            if ( os.path.exists( custom_favicon ) ): favicon = custom_favicon
            
        pixbuf = gtk.gdk.pixbuf_new_from_file( favicon )
        cell.set_property("pixbuf", pixbuf)
        
    def fixed_toggled(self, cell, path, treeview):        
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

