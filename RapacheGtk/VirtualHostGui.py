#!/usr/bin/env python

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

from RapacheCore.VirtualHost import *
from RapacheGtk import GuiUtils
        
class VirtualHostWindow:
    
    create_new = True
    name = None
    
    def __init__ ( self, gladepath, father = None):
        self.father = father
        self.gladefile = gladepath + "/" + "edit_vhost.glade"  
        self.xml = gtk.glade.XML(self.gladefile)     
        #Create our dictionary and connect it
        dic = { 
            "quit" : self.quit
            , "on_ok":self.save
            , "on_cancel":self.close  
            , "domain_name_updated":self.domain_name_updated
            , "custom_folder_toggled":self.custom_folder_toggled
            }
        self.xml.signal_autoconnect(dic)
        self.xml.get_widget( 'custom_folder' ).set_action ( gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER )                
        font_desc = pango.FontDescription('monospace')
        self.xml.get_widget( 'vhost_source' ).modify_font(font_desc)
        GuiUtils.style_as_tooltip( self.xml.get_widget( 'message_container' ) )
   
    def load (self, name ):

        site = VirtualHostModel( name )
        self.create_new = False
        self.name = name 
        self._get( 'create_hosts_entry' ).hide()
        self._get( 'create_hosts_label' ).hide()
        try:
            site.load()
            self._get( 'has_www' ).set_active( site.data[ 'has_www' ] )
            self._get( 'domain_name' ).set_text( site.data[ 'domain_name' ] )
            self._get( 'default_folder' ).set_text( site.data[ 'target_folder' ] )
            self.xml.get_widget( 'ok_button' ).set_sensitive(True);
        except "VhostUnparsable":            
            self._get( 'notebook' ).get_nth_page( 0 ).hide()
        buffer = self.xml.get_widget( 'vhost_source' ).get_buffer()
        buffer.set_text( site.get_source() )
    def _get(self, id ):
        return self.xml.get_widget( id )
    
    
    def error ( self, message ):
        self.xml.get_widget( 'message_text' ).set_label( '<b>'+message+'</b>' )
        self.xml.get_widget( 'message_container' ).show()
        
    def quit (self, widget):      
        self.father.new_vhost_window = None
    
    def close ( self, widget = None ):
        self.window = self.xml.get_widget( 'vhost_edit_window' )
        self.window.destroy()
    def domain_name_updated ( self, widget, a = None, b = None, c = None ):
        name = widget.get_text()
        if ( valid_domain_name( name ) ):
            self.xml.get_widget( 'ok_button' ).set_sensitive(True);
            if self.create_new :
                self.xml.get_widget( 'default_folder' ).set_text( '/var/www/'+name+'/httpdocs' )
        else:
            self.xml.get_widget( 'ok_button' ).set_sensitive(False);
    def custom_folder_toggled( self, widget ):
        if ( widget.get_active() == True ):
            self.xml.get_widget( 'custom_folder' ).show()
            self.xml.get_widget( 'default_folder' ).hide()
        else:
            self.xml.get_widget( 'custom_folder' ).hide()
            self.xml.get_widget( 'default_folder' ).show()            
    
    
    def save( self, widget ):
        options = {}
        options[ 'has_www' ] = self.xml.get_widget( 'has_www' ).get_active()     
        options[ 'domain_name' ] = ( self.xml.get_widget( 'domain_name' ).get_text() )
        options[ 'hack_hosts' ] = self.xml.get_widget( 'create_hosts_entry' ).get_active()                
        if self.xml.get_widget( 'set_custom_folder' ).get_active():
            target_folder =  self.xml.get_widget( 'custom_folder' ).get_filename ()     
        else:
            target_folder =  self.xml.get_widget( 'default_folder' ).get_text()
        options[ 'target_folder' ] = target_folder
                       
        
        try:
            if ( self.create_new ):
                site = VirtualHostModel( options[ 'domain_name' ] )
                site.create ( options )
            else:
                print "Current name:", self.name
                site = VirtualHostModel( self.name )
                site.update( options, self.name )
            
            self.father.create_vhost_list()        
            self.father.please_restart()
            self.close()
        except "VhostExists":
           print "========================"
           self.error( "A virtual host with the same name already exists" )     
        
             
        return True
