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

import sys
import os
import re

from LineElement import *
from RapacheCore import Configuration
#from RapacheCore.ApacheConf import *
#from RapacheCore.ApacheParser import ApacheParser as Parser

from RapacheCore.ApacheParser import VhostParser
from RapacheCore.ApacheParser import VhostNotFound

from RapacheCore.HostsManager import HostsManager
from RapacheCore import Shell

VHOST_TEMPLATE = """#created for you by Rapache
<VirtualHost *>
    #ServerAdmin webmaster@example.com
    ServerName example
    DocumentRoot /var/www/examplepath
</VirtualHost>"""


def valid_domain_name ( name ):
    # TODO: fix regular expression 
    valid = ( re.search( '^[a-zA-Z0-9.-]+$', name ) != None )
    return valid

def is_denormalized_vhost ( fname ):
    try:           
        flink = Shell.command.readlink( os.path.join(Configuration.SITES_ENABLED_DIR, fname))
        flink = os.path.join(os.path.dirname( Configuration.SITES_AVAILABLE_DIR ), flink)
        #no exceptions ? Means it's a link        
        return True
    except:        
        return False
    return False
def is_not_normalizable( fname):
     dest = os.path.join(Configuration.SITES_AVAILABLE_DIR, fname)
     return Shell.command.exists( dest )
 
def normalize_vhost( fname ):
    print "Normalizing:", fname
    orig = os.path.join(Configuration.SITES_ENABLED_DIR, fname)
    dest = os.path.join(Configuration.SITES_AVAILABLE_DIR, fname)
    if ( Shell.command.exists( dest ) == True ):
        print fname, "already exists in available dir. not even trying"
        return False
    command = ['mv',orig,dest]
    code, output, error = Shell.command.sudo_execute( command )
    return ( code == 0 )
    return  Shell.command.exists( dest )


# Replacment that uses new parser.....
class VirtualHostModel():
    def __init__(self, name = None, plugin_manager = None):        
        self.__name = name
        self.__parser = Parser() 
        self.__is_default = name == "default"
        self.is_new = name == "" or not Shell.command.exists( self.get_source_filename() )
        self.data = None
        self.parsable = True
        self.enabled = self.is_enabled()
        self.hack_hosts = False
        self.config = None
        
        if  self.is_new:
            self.__parser = Parser()
            self.__parser.set_from_str( VHOST_TEMPLATE )
            self.config = self.__parser.virtualhost
        else:
            try:
                self.load(None)
                self.parsable = True

                if self.__name != self.get_server_name():
                    print "FILE NAME MISMATCH"
                    print self.__name
                    print self.get_server_name()
            except:
                pass
    # IO Methods
    def load(self, name = False):  
        try:
            self.__parser = Parser()
            self.__parser.load( self.get_source_filename() )
            self.config = self.__parser.rsearch("VirtualHost")[0]
            return True
        except:
             self.parsable = False
             return False
             
    def load_from_string(self, content):
        current_parser = self.__parser
        try:
            self.__parser = Parser()
            self.__parser.set_from_str( content )
            self.config = self.__parser.rsearch("VirtualHost")[0]
            return True
        except:
            self.__parser = current_parser
            return False
         
    def save(self, content=None):
        if not Shell.command.ask_password(): return 
        
        # Get parser content
        if not content: content = self.__parser.get_as_str()
        
        DocumentRoot = self.get_document_root()
        ServerName = self.get_server_name()
        
        print "Creating virtualhost: " + ServerName
        print "Folder: " + DocumentRoot
        
        if ( Shell.command.exists( DocumentRoot ) == False ): 
            print "Folder " + DocumentRoot + " does not exist"        
            Shell.command.create_complete_path( DocumentRoot )
            
        if ( Shell.command.exists( DocumentRoot ) == False ):
            self.error( "Could not create target folder" ) #TODO fix this
            return False
                       
        if ( valid_domain_name( ServerName ) == False ):
            self.error ( 'Bad domain name: '+ ServerName )
            return False
        
        # if new then make sure to update name before saving
        if self.is_new: self.__name = ServerName

        Shell.command.write_file(self.get_source_filename(), content)
          
        if self.hack_hosts:
            Shell.command.sudo_execute ( [os.path.join(Configuration.APPPATH, "hosts-manager"), '-a', ServerName ] )
            for alias in self.config.ServerAlias:
                Shell.command.sudo_execute ( [os.path.join(Configuration.APPPATH, 'hosts-manager'), '-a', alias ])
        
        if self.is_new:      
            self.toggle( True ) #activate by default 
            self.is_new = False
        else:
            # If already existed may need to rename the file
            
            old_enabled = self.is_enabled()
            
            new_name = os.path.join(Configuration.SITES_AVAILABLE_DIR, ServerName)
            old_name = os.path.join(Configuration.SITES_AVAILABLE_DIR, self.__name)
            
            print "old name", old_name
            print "new name", new_name
            
            if old_name != new_name and Shell.command.exists( new_name ) == False:
                print "Server name changed, updating conf filename"
                self.toggle( False )     
                Shell.command.move( old_name, new_name )
                if Shell.command.exists( new_name ) == True:
                    # success ! we need to reload vhost with the new name
                    self.__name = ServerName
                    self.load()
                    #...so we can toogle it on again
                    if old_enabled == True: 
                        print "Re-activating"
                        self.toggle( True )
                    else:
                        print "Skipping activation"
                else:
                    print "error! not created:", new_name  
                    
        return True  

    def get_source ( self ):
        return Shell.command.read_file(self.get_source_filename())
        
    def get_source_generated( self ):
        return self.__parser.get_as_str()
     
    def get_name(self):
        return self.__name
    def get_source_filename(self):
         return os.path.join(Configuration.SITES_AVAILABLE_DIR, self.__name)

    def get_backup_files(self):
            return Shell.command.get_backup_files(  os.path.join(Configuration.SITES_AVAILABLE_DIR, self.__name))
    def get_source_version ( self, timestamp ):
        return Shell.command.read_file_version(self.get_source_filename(), timestamp)

    def delete( self ):
        "Deletes a VirtualHost configuration file"
        if not self.is_new:
            if ( self.is_enabled() ): 
                self.toggle( False )
            Shell.command.sudo_execute( [ 'rm', self.get_source_filename() ])

    def is_default( self ):
        return self.__is_default

    def is_editable( self ):
        return (self.parsable and not self.config == None)

    def is_enabled ( self ):
        orig = self.get_source_filename()
        dirList = Shell.command.listdir( Configuration.SITES_ENABLED_DIR )
        for fname in dirList:
            try:                                
                flink = Shell.command.readlink( os.path.join(Configuration.SITES_ENABLED_DIR, fname) )               
                flink = os.path.join(os.path.dirname( Configuration.SITES_ENABLED_DIR +"/" ), flink)
                # please note debian features a nice set of
                # mixed absolute and relative links. FREAKS !
                # the added "/" is also necessary
                flink = os.path.normpath(flink)               
                if ( flink == orig ):
                    return True
            except:
                pass
          
        return False
        
    def toggle( self, status ):
        "status = True|False"
        if status:
            command = "a2ensite"
        else :
            command = "a2dissite" 
                   
        # set new value
        Shell.command.sudo_execute( [ command, self.__name ] )
        self.enabled = self.is_enabled()
        self.changed = True    

        
    # There are a number of fields we will use often, we will add handlers for them
    def get_server_name(self):
        try:
            if self.config.ServerName:
                return self.config.ServerName.value
        except:
            pass
        return self.__name
        
    def get_document_root(self):
        try:
            if self.config.DocumentRoot:
                return self.config.DocumentRoot.value
        except:
            pass
        return None
            
    def get_server_alias(self):
        try:
            if self.config.ServerAlias:
                return self.config.ServerAlias.opts
        except:
            pass
        return []    

    def get_icon(self):
        # TODO: This MUST return a local path...
        # TODO: Try url for a favicon as well
        DocumentRoot = self.get_document_root()
        if DocumentRoot != None:
                favicon = os.path.join(DocumentRoot, "favicon.ico")
                if ( os.path.exists( favicon ) ): 
                    return favicon
        return os.path.join( Configuration.GLADEPATH, 'browser.png' )
    
    
    def has_port(self):
        value = self.config.value
        if value is None: return False
        tokens = value.split(':')
        if len(tokens) < 2: return False
        if tokens[-1] =="*": return False
        return True
    
    
    def get_port(self):
        value = self.config.value
        if value is None: return None
        tokens = value.split(':')
        if len(tokens) < 2: return None
        if tokens[-1] =="*": return None
        return int(tokens[-1])

    def set_port(self, portnumber):
        value = self.config.value
        old_port = self.get_port()
        if str(portnumber) == str(old_port):
            return #no changes needed
        if portnumber is not None:
            if old_port is None: 
                value += ":"+str(portnumber)
            else:
                tokens = value.split(':')
                tokens[-1] = str( portnumber )
                value = ":".join( tokens )
        else: 
            #old_port can't be None because of the condition:
            #if str(portnumber) == str(old_port)
            #at the top of this method
            tokens = value.split(':')
            tokens[-1] = str( portnumber )
            value = ":".join( tokens[:-1] )
        self.config.value = value
