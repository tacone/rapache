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

import gtk
import gobject
from CheckListView import *
import os
import re
from RapacheCore.VirtualHost import *
from RapacheCore import Module
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
        self.toggled_callback = self.__fixed_toggled
    
    
    def load(self):
        self.items = {}
        site_template = "<b><big>%s</big></b>\n<small>DocumentRoot: %s</small>"
        site_unparsable_template = "<b><big>%s</big></b>\n<small><i>Further information not available</i></small>"
        
        lstore = self._reset_model()
            
        data = []
        dirList=os.listdir( Configuration.SITES_AVAILABLE_DIR )
        dirList = [x for x in dirList if self._blacklisted( x ) == False ]            
        for fname in  dirList :                        
            site = VirtualHostModel( fname )
            if not site.is_new:
                self.items[ fname ] = site
                            
        for idx in sorted( self.items ):
            site = self.items[ idx ]
            if ( site.parsable ):
                markup = site_template \
                % ( site.get_server_name(), site.get_document_root() )
            else:
                markup = site_unparsable_template % site.get_display_name()
            iter = lstore.append()
            
            favicon = site.get_icon()
            pixbuf = gtk.gdk.pixbuf_new_from_file( favicon )
                       
            lstore.set(iter,
                COLUMN_FIXED, site.enabled,
                COLUMN_ICON, pixbuf,
                COLUMN_SEVERITY, site.get_server_name(),
                COLUMN_MARKUP, markup )

    def __fixed_toggled(self, cell, path, treeview):        
        # get toggled iter        
        model = treeview.get_model()
        iter = model.get_iter((int(path),))
        fixed = model.get_value(iter, COLUMN_FIXED)
        name = model.get_value(iter, COLUMN_SEVERITY)

        fixed = not fixed        
        if fixed:
            Shell.command.sudo_execute ( [Configuration.APPPATH+'/hosts-manager', '-a',name])
        else :
            Shell.command.sudo_execute ( [Configuration.APPPATH+'/hosts-manager', '-r',name])
        # set new value        
        site = VirtualHostModel( name )
        site.toggle( fixed )
        model.set(iter, COLUMN_FIXED, site.enabled )        
        if ( site.changed ):
            self.raise_event( 'please_restart_apache' )                
gobject.type_register (VhostsTreeView)

class DenormalizedVhostsTreeView ( ConfFilesTreeView ):
    def __init__ (self, *args, **kwargs):
        super (DenormalizedVhostsTreeView, self).__init__ (*args, **kwargs)
        #print self.column_checkbox, self.column_description, self.column_icon
        self.column_checkbox.set_visible( False )
        self.column_icon.get_cell_renderers()[0].set_property( 'stock-id',  gtk.STOCK_DIALOG_WARNING )        
    def load(self):    
        self.items = {}
        site_template = "<b><big>%s</big></b>"        
        lstore = self._reset_model()
        
        data = []  
        dirList=os.listdir( Configuration.SITES_ENABLED_DIR )
        dirList = [x for x in dirList if self._blacklisted( x ) == False ]
        dirList = [x for x in dirList if is_denormalized_vhost( x ) == False ]             
        
        self.items = {}
        for fname in  dirList :
            site = VirtualHostModel( fname )                        
            self.items[ fname ] = site
            site = None        
        for idx in sorted( self.items ):            
            site = self.items[ idx ]            
            normalizable = not is_not_normalizable(site.get_name())
            markup = site_template % site.get_name()
            if ( normalizable == False ):
                markup = markup + " CANNOT FIX"
            iter = lstore.append()
            
            lstore.set(iter,
                COLUMN_FIXED, normalizable,
                COLUMN_SEVERITY, site.get_name(), 
                COLUMN_MARKUP, markup 
                )
                
    def toggled_callback(self, *args, **kwargs):
        pass
gobject.type_register (DenormalizedVhostsTreeView )

class ModulesTreeView ( ConfFilesTreeView ):
    def __init__ (self, *args, **kwargs):
        super (ModulesTreeView, self).__init__ (*args, **kwargs)
        
        icon_file_name = os.path.join( Configuration.GLADEPATH , "modules.png")
        pixbuf = gtk.gdk.pixbuf_new_from_file( icon_file_name )
        
        self.column_icon.get_cell_renderers()[0].set_property('pixbuf', pixbuf) 
        self.toggled_callback = self.__fixed_toggled
        self.selected_callback = self.__selected
        self.column_description.get_cell_renderers()[0].set_property('wrap-mode', gtk.WRAP_WORD)
        self.column_description.get_cell_renderers()[0].set_property('wrap-width', 400)
    def __selected(self, *args, **kwargs ):
        print "MODULE NAME:", self.get_selected_line()
        print "DEPENDANTS: ", Module.get_module_dependants(self.get_selected_line(), self.items)
    def load(self):
        self.items = {}
        mod_template = "<b><big>%s</big></b>"
        mod_unparsable_template = "<b><big>%s</big></b>\n<small><i>Further information not available</i></small>"
        lstore = self._reset_model()
        data = []  
        
        """dirList=os.listdir( Configuration.MODS_AVAILABLE_DIR )
        dirList = [x for x in dirList if self._blacklisted( x ) == False ]            
        for fname in  dirList :                        
            mod = Module.ModuleModel( fname )
            try:
                mod.load()
            except "VhostUnparsable":
                pass
            self.items[ fname ] = mod
            mod = None
        """
        self.items = Module.module_list()

        for idx in sorted( self.items ):
            mod = self.items[ idx ]
            if ( mod.parsable ):
                markup = mod_template \
                % ( mod.data['name'] ) #, mod.data[ 'DocumentRoot' ] )
                markup += "\n<small>%s</small>" % mod.data[ 'description' ]
                if len( mod.data[ 'dependancies' ] ) > 0:
                    markup += "\n<small><b>%s</b></small>" % ( "Dependencies: " + \
                    ", ".join( mod.data[ 'dependancies' ] ) )
                else:
                    markup += "\n<small><i>No dependencies</i></small>"
            else:
                markup = mod_unparsable_template % mod.data['name']
            iter = lstore.append()
            lstore.set(iter,
                COLUMN_FIXED, mod.data['enabled'],
                COLUMN_SEVERITY, mod.data['name'],
                COLUMN_MARKUP, markup )
            
    def __fixed_toggled(self, cell, path, treeview):        
        # get toggled iter        
        model = treeview.get_model()
        iter = model.get_iter((int(path),))
        fixed = model.get_value(iter, COLUMN_FIXED)
        name = model.get_value(iter, COLUMN_SEVERITY)
        fixed = not fixed        
        # set new value        
        mod = Module.ModuleModel( name )
        mod.toggle( fixed )
        model.set(iter, COLUMN_FIXED, mod.data['enabled'] )
        if ( mod.changed ):
            self.raise_event( 'please_restart_apache' ) 
        self.raise_event( 'please_reload_lists', {}, True ) 

gobject.type_register ( ModulesTreeView )



class ErrorsTreeView ( ConfFilesTreeView ):
    def __init__ (self, *args, **kwargs):
        super (ErrorsTreeView, self).__init__ (*args, **kwargs)
        #print self.column_checkbox, self.column_description, self.column_icon
        self.column_checkbox.set_visible( True )        
        self.column_description.get_cell_renderers()[0].set_property('wrap-width', 500)  
        self.column_checkbox.get_cell_renderers()[0].set_property( 'activatable', False )
    def load(self, apache):    
        self.items = {}
        site_template = "<b><big>%s</big></b>"        
        lstore = self._reset_model()        
        res, text = apache.test_config()
        # -1 = nothing to fix
        # 0  = nothing auto-fixable
        # 1 = something to be done
        returncode = -1
        
        if not res:       
            returncode = 0
            iter = lstore.append()
            markup = site_template % "Apache Config Error"
            
            pixbuf = self.render_icon(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_LARGE_TOOLBAR)
            
            lstore.set(iter,
                COLUMN_ICON, pixbuf,
                COLUMN_FIXED, False,
                COLUMN_SEVERITY, "Apache Config Error",
                COLUMN_MARKUP, markup + "\n" + text +"\n<small><i>You must resolve this error to restart apache</i></small>"
                )
        fixable_items = self._add_denormalized_vhosts()
        return max( returncode,  fixable_items )
    def unused(self):
        data = []  
        dirList=os.listdir( Configuration.SITES_ENABLED_DIR )
        dirList = [x for x in dirList if self._blacklisted( x ) == False ]
        #dirList = [x for x in dirList if is_denormalized_vhost( x ) == False ]                   
        for fname in  dirList :
            site = VirtualHostModel( fname )                        
            self.items[ fname ] = site
            site = None

        for idx in sorted( self.items ):            
            site = self.items[ idx ]
            normalizable = not is_not_normalizable(site.get_server_name())
            markup = site_template % site.get_server_name()
            
            
            if ( normalizable == False ):
                markup = markup + " CANNOT FIX"
            iter = lstore.append()
            
            pixbuf = self.render_icon(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_LARGE_TOOLBAR)
            
            lstore.set(iter,
                COLUMN_ICON, pixbuf,
                COLUMN_FIXED, normalizable,
                COLUMN_SEVERITY, site.get_server_name(),
                COLUMN_MARKUP, markup +  "\nThe virtual host file is only present inside /etc/apache/sites-enabled.\n<small><i>You must normalize in order to manage this host</i>.</small>"
                )
         
    def _add_denormalized_vhosts( self ):
        
        site_template = "<b><big>%s</big></b>"              
        lstore = self.get_model()
        data = []  
        dirList=os.listdir( Configuration.SITES_ENABLED_DIR )
        dirList = [x for x in dirList if self._blacklisted( x ) == False ]
        dirList = [x for x in dirList if is_denormalized_vhost( x ) == False ]    
        print "=============="
        print "-->", "denormalized list:",  dirList
        self.items = {}
        fixable_items = 0
        
        for fname in  dirList :
            site = VirtualHostModel( fname )                        
            self.items[ fname ] = site
            site = None        
        for idx in sorted( self.items ):            
            site = self.items[ idx ]            
            normalizable = not is_not_normalizable(site.get_name())
            markup = site_template % site.get_name()
            if ( normalizable == False ):
                markup = markup + " CANNOT FIX"
            else:
                fixable_items += 1
            iter = lstore.append()
            pixbuf = self.render_icon(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_LARGE_TOOLBAR)
            lstore.set(iter,
                COLUMN_ICON, pixbuf,
                COLUMN_FIXED, normalizable,
                COLUMN_SEVERITY, site.get_server_name(),
                COLUMN_MARKUP, markup +  "\nThe virtual host file is only present inside /etc/apache/sites-enabled.\n<small><i>You must normalize in order to manage this host</i>.</small>"
                )
        
        if not len(lstore): return -1
        return fixable_items
            
                
    def toggled_callback(self, *args, **kwargs):
        pass
#gobject.type_register (DenormalizedVhostsTreeView )
