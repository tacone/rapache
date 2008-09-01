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

        self.is_new = name == "" or not Shell.command.exists( self.get_source_filename() )
        self.data = None
        self.parsable = True
        self.enabled = self.is_enabled()
        self.hack_hosts = False
        if not self.is_new:
            self.load(None)

    # IO Methods
    def load(self, name = False):  
        #try:
            self.__parser = Parser()
            self.__parser.load( self.get_source_filename() )
            self.config = self.__parser.virtualhost
            return True
        #except:
        #     self.parsable = False
        #     return False
             
    def load_from_string(self, content):
        #try:
        self.__parser = Parser()
        self.__parser.set_from_str( content )
        self.config = self.__parser.virtualhost
        return True
        #except:
        #     self.parsable = False
        #     return False
         
    def save(self, content=None):
        
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
            return self.config.ServerName.value
        except:
            return self.__name
        
    def get_document_root(self):
        try:
            return self.config.DocumentRoot.value
        except:
            return None
            
    def get_server_alias(self):
        try:
            return self.config.ServerAlias.opts
        except:
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

        
# Replacment that has a bit of state
class VirtualHostModelOld():
    def __init__(self, name = None, plugin_manager = None):
        self.data = {
              'ServerName' : name        
            , 'DocumentRoot' : None            
        }
        self.__content = ""        
        self.__name = name # save the original name
        self.changed = False
        self.is_new = name == "" or not Shell.command.exists( self.get_source_filename() )
        self.enabled = self.is_enabled()
        self.hack_hosts = False
        self.parsable = True

        # Init plugin values so the keys exist
        if plugin_manager:
            for plugin in plugin_manager.plugins:
                for key in plugin.vhosts_config.keys():
                        self.data[ key ] = None        

        if not self.is_new:
            self.load(None, plugin_manager)

    # Shorcut for getting data value 
    def get_value(self, key, default=None):
        if self.data.has_key( key ):
            if self.data[key]:
                return self.data[key]
        return default
        
    def set_value(self, key, value):    
        self.data[key] = value

    # Returns a label for displaying in UI
    def get_display_name(self):
        return self.get_value("ServerName", self.__name)

    def get_source ( self ):
        return Shell.command.read_file(self.get_source_filename())
        
    def get_source_generated( self, content=None ):
        return self.__update(content)
        
    def get_source_filename(self):
         return os.path.join(Configuration.SITES_AVAILABLE_DIR, self.__name)

    def get_backup_files(self):
            return Shell.command.get_backup_files(  os.path.join(Configuration.SITES_AVAILABLE_DIR, self.__name))
    def get_source_version ( self, timestamp ):
        return Shell.command.read_file_version(self.get_source_filename(), timestamp)
 
    def is_enabled ( self ):
        orig = self.get_source_filename()
        dirList=Shell.command.listdir( Configuration.SITES_ENABLED_DIR )
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

    def load_from_string(self, content, plugin_manager = None):
        parser = Parser()
        parser.set_content_from_string(content)
        return self.__load( parser, plugin_manager)
    
    def load(self, name = False, plugin_manager = None):  
        parser = Parser()
        try:
            parser.load( self.get_source_filename() )
            return self.__load( parser, plugin_manager)
        except VhostNotFound:
             self.parsable = False
             return False
        

    def __load(self, parser, plugin_manager = None):
        options = {}        
        piece = VhostParser( parser )        
        domain_name = piece.get_value( 'ServerName' )
        if domain_name == None:
            self.parsable = False
            if self.__name == "default":  
                domain_name = self.__name
             #return False
        options[ 'ServerName' ] = domain_name
        options[ 'ServerAlias' ] = piece.get_options( 'ServerAlias' )
        options[ 'DocumentRoot' ] = piece.get_value('DocumentRoot')
        hosts = HostsManager()
        if ( domain_name == None or hosts.find ( domain_name ) == False ):
            options['hack_hosts'] = False
        else:
            options['hack_hosts'] = True
        self.parsable = True
        
        # Load plugin values

        if plugin_manager:
            for plugin in plugin_manager.plugins:
                for key in plugin.vhosts_config.keys():
                    if plugin.vhosts_config[key] == 1:
                        options[ key ] = piece.get_options( key )
                    else:
                        options[ key ] = piece.get_value( key )
        
        self.data.update( options )
        
        return True
    
    def __update(self, content=None):
        parser = Parser()
        if not content:
            if self.is_new:
                parser.set_content_from_string( VHOST_TEMPLATE )
            else:
                 parser.load( self.get_source_filename() )
        else:
             parser.set_content_from_string(content)

        piece = VhostParser( parser )

        # Get a bit more dynamic with it
        for key in self.data.keys():
            obj = self.data[key]
            if isinstance(obj, list):
                #piece.set_value(key, None)
                for opt in obj:
                    piece.add_option(key, opt )
            elif isinstance(obj, str):
                if obj:
                    piece.set_value(key, obj)
                else:
                    piece.remove_value(key)


        
        return "".join(parser.get_content())      
                
    def save(self, content=None):
        print "Creating virtualhost: "+ self.data['ServerName']
        print "Folder: " + self.data['DocumentRoot']
        
        if ( Shell.command.exists( self.data['DocumentRoot'] ) == False ): 
            print "Folder " + self.data['DocumentRoot']+" does not exist"        
            Shell.command.create_complete_path( self.data['DocumentRoot'] )
            
        if ( Shell.command.exists( self.data['DocumentRoot'] ) == False ):
            self.error( "Could not create target folder" ) #TODO fix this
            return False
                       
        if ( valid_domain_name( self.data['ServerName'] ) == False ):
            self.error ( 'Bad domain name: '+ self.data['ServerName'] )
            return False
        
        # if new then make sure to update name before saving
        if self.is_new:
            self.__name = self.data['ServerName']

        Shell.command.write_file(self.get_source_filename(), self.__update(content))
          
        if self.hack_hosts:
            Shell.command.sudo_execute ( [os.path.join(Configuration.APPPATH, "hosts-manager"), '-a', self.data['ServerName'] ] )
            for alias_name in self.data[ 'ServerAlias' ]:
                Shell.command.sudo_execute ( [os.path.join(Configuration.APPPATH, 'hosts-manager'), '-a',alias_name ])
        self.changed = True  
        
        if self.is_new:      
            self.toggle( True ) #activate by default 
            self.is_new = False
        else:
            # If already existed may need to rename the file
            
            old_enabled = self.is_enabled()
            
            new_name = os.path.join(Configuration.SITES_AVAILABLE_DIR, self.data['ServerName'])
            old_name = os.path.join(Configuration.SITES_AVAILABLE_DIR, self.__name)
            
            print "old name", old_name
            print "new name", new_name
            
            if old_name != new_name and Shell.command.exists( new_name ) == False:
                print "Server name changed, updating conf filename"
                self.toggle( False )     
                Shell.command.move( old_name, new_name )
                if Shell.command.exists( new_name ) == True:
                    #success ! we need to reload vhost with the new name
                    
                    self.__name =  self.data['ServerName']
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
        
    def get_icon(self):
        # TODO: This MUST return a local path...
        # TODO: Try url for a favicon as well
        if self.data['DocumentRoot'] != None:
                favicon = os.path.join(self.data['DocumentRoot'], "favicon.ico")
                if ( os.path.exists( favicon ) ): 
                    return favicon
        return os.path.join( Configuration.GLADEPATH, 'browser.png' )

    def delete( self ):
        "Deletes a VirtualHost configuration file"
        if not self.is_new:
            if ( self.is_enabled() ): 
                self.toggle( False )
            Shell.command.sudo_execute( [ 'rm', self.get_source_filename() ])




