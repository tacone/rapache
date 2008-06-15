#!/usr/bin/env python
#
# Copyright (C) Stefano Forenza 2008 <tacone@gmail.com>
# 
# This file is free software: you can redistribute it and/or modify it
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

import sys
import os
import tempfile
import re
from RapacheCore import Configuration
from RapacheCore.ApacheConf import *
from RapacheCore.HostsManager import HostsManager

        
VHOST_TEMPLATE = """#created for you by Rapache
<VirtualHost *>
	ServerAdmin webmaster@||example||
	ServerName ||example||
	#ServerAlias www.||example||
	DocumentRoot ||target_folder||
	Options Indexes FollowSymLinks MultiViews		
	<Directory ||target_folder||>
		AllowOverride All
		Order allow,deny
		allow from all
	</Directory>
</VirtualHost>"""


def valid_domain_name ( name ):
    # TODO: fix regular expression 
    valid = ( re.search( '^[a-zA-Z0-9.-]+$', name ) != None )
    return valid
       
class VirtualHostModel:
    
    def __init__(self, name = None):
        self.defaults = {
            'enabled' : False
            , 'name' : None
            , 'domain_name': None
            , 'changed' : False
            , 'has_www' : False
            , 'hack_hosts' : False
            , 'target_folder' : None            
        }
        self.data = {}
        self.parsable = False
        self.changed = False
        self.simulation = False
        
        self.data = self.defaults
        if ( name != None ):
            self.data[ 'name' ] = name
            self.data[ 'enabled' ] = self.is_enabled()

    def _search(self, content, regexp ): 
        content = content.split( "\n" )           
        for line in content:
            match = re.search( regexp , line, re.IGNORECASE )            
            if ( match != None ) :
                if match != False:
                    #print regexp+" " +line
                    #print match
                    return match            
        return False
    
    def _get_conf_value(self, content, regexp):        
        match = self._search(content, regexp )
        if ( match == False or match == None ): return None
        found_entry = match.groups()                          
        found_value = found_entry[0]
        return found_value
 
    def load (self, name = False):
       
        try:
            #reset everything
            print "Loading :\t",name
            if ( name == False ): name = self.data[ 'name' ]
            self.data = self.defaults   
            self.data['name'] = name
            
            print "Loading(b) :\t",self.data[ 'name' ]            
            options = {}
            content = self.get_source()        
            #domain_name = self._get_domain_name(content)
            domain_regexp = r'^\s*ServerName\s+([A-Za-z0-9.\-_]*)'
            domain_name = self._get_conf_value(content, domain_regexp)
            options[ 'domain_name' ] = domain_name
            domain_regexp = domain_name.replace( '.', '\\.' ) #quote for regexp
            www_regexp = r'^\s*ServerAlias\s*[^#]*\s+www\.'+domain_regexp+'(\s*|$)'
            folder_regexp = domain_regexp = r'^\s*DocumentRoot\s+(\S+\s*\S+)'
            
            print "Domain Name :\t"+domain_name             
            if self._search(content, www_regexp ) != None \
            and self._search(content, www_regexp ) != False  :
                options[ 'has_www' ] = True
            else:
                options[ 'has_www' ] = False 
    
            print "Has www :\t"+str(options[ 'has_www' ])
                
            options[ 'target_folder' ] = self._get_conf_value(content, folder_regexp)
            
            print "Document Root :\t"+str( options[ 'target_folder' ] )
            hosts = HostsManager()
            print domain_name
            if ( hosts.find ( domain_name ) == False ):
                options['hack_hosts'] = False
            else:
                options['hack_hosts'] = True
            self.parsable = True
        except:
            print "Unparsable by me - unsupported"
            raise "VhostUnparsable"
            return False
        self.data.update( options )
        print self.data
        return True
        
    def is_enabled ( self ):
        orig = self.data[ 'name' ]        
        dirList=os.listdir(  Configuration.SITES_ENABLED_DIR )
        for fname in dirList:
            try:                                
                flink = os.readlink( Configuration.SITES_ENABLED_DIR +"/"+fname )
                flink = os.path.join(os.path.dirname( Configuration.SITES_ENABLED_DIR ), flink)                
                if ( flink == Configuration.SITES_AVAILABLE_DIR+"/"+orig ):
                    return True
            except:
                1
          
        return False
    def _command ( self, command ):
        print "COMMAND: "+command
        return os.system( command )
    def toggle( self, status ):
        "status = True|False"
        if status:
    	    command = "a2ensite"
        else :
    	    command = "a2dissite"        
        # set new value
        command = "gksudo "+command+" "+self.data['name']
        if self.simulation:
            print "SIMULATED "+command
            self.data['enabled'] = status
        else:
            self._command( command )
            self.data['enabled'] = self.is_enabled()
        self.changed = True
        
    def delete( self ):
        "Deletes a VirtualHost configuration file"
        if ( self.is_enabled() ): self.toggle( False )
        self._command( 'gksudo rm '+Configuration.SITES_AVAILABLE_DIR+'/'+self.data['name'] )
    def _create_complete_path ( self, complete_path ):
        print "Attempting to create: " + complete_path
        tokens = complete_path.split( '/' )
        del tokens[ 0 ]        
        path = ''
        for piece in tokens:
            path = path + '/' + piece
            if ( os.path.exists( path ) == False ):
                try:
                    self._command( 'gksudo "mkdir '+path+'"' )
                except:
                    print "error on creating path"+path
                    return False                   
        print "Created path: " + path
        return True    
     
    def get_source ( self ):
        file = open( Configuration.SITES_AVAILABLE_DIR+'/'+self.data['name'], 'r' )
        content = file.read()
        file.close()
        return content
    def update ( self, new_options, name ):
        print "updating virtual host", name
        #print new_options        
        
        old_enabled = self.is_enabled()
        print "IS ENABLED", old_enabled
        
        parser = Parser()
        parser = Parser()
        parser.load(  Configuration.SITES_AVAILABLE_DIR+'/'+name )
        piece = VhostParser( parser )
        old_servername = piece.get_value( 'ServerName' )
        old_www = "www."+old_servername
        new_www = "www."+new_options['domain_name']
        piece.remove_option( 'ServerAlias', old_www )        
        if new_options['has_www'] == True:
            print "WWW (ServerAlias) From",piece.has_option('old_www', old_www ),"to", new_www         
            piece.add_option( 'ServerAlias', new_www)
        else:            
            print "WWW From",piece.has_option('old_www', old_www ),"to <Nothing>"                                    
        print "DocumentRoot From",piece.get_value('DocumentRoot' ),"to",new_options['target_folder']
        piece.set_value('DocumentRoot', new_options['target_folder'] )
                
        print "ServerName From",piece.get_value('ServerName' ),"to",new_options['domain_name']
        piece.set_value('ServerName', new_options['domain_name'] )                
        complete_path = Configuration.SITES_AVAILABLE_DIR+'/'+ name 
        
        print "Writing.."
        print parser.get_source()
        self._write( complete_path, parser.get_source() )
        
        #if the servername coincides with the configuration filename
        #we try to stick with the convention
        new_name = Configuration.SITES_AVAILABLE_DIR + "/"+ new_options['domain_name']
        old_name = Configuration.SITES_AVAILABLE_DIR + "/"+ old_servername
        print "old name", old_name
        print "new name", new_name
        if old_name != new_name and os.path.exists( new_name ) == False:
            print "Server name changed, updating conf filename"
            self.toggle( False )     
            self._command( 'gksudo mv "'+old_name+'" "'+new_name+'"' )
            if os.path.exists( new_name ) == True:
                #success ! we need to reload vhost with the new name
                self.load( new_options['domain_name'] )
                #...so we can toogle it on again
                if old_enabled == True: 
                    print "Re-activating"
                    self.toggle( True )
                else:
                    print "Skipping activation"
            else:
                print "error! not created:", new_name
        return True
    def _write(self, complete_path, content ):    
        tempfilename = tempfile.mktemp()
        print "creating temporary file "+tempfilename
        logfile = open( tempfilename , 'w')
        logfile.write( content )
        logfile.close()
        command = "gksudo cp "+tempfilename+" "+complete_path
        print "copying tempfile in the appropriate location: "+command
        self._command( command )
        
        
    def create ( self, new_options ):                
        
        options = self.data
        options.update( new_options )        
        
        #as of creation-time name is not expected to be in options
        options['name'] = options[ 'domain_name' ]
        complete_path = Configuration.SITES_AVAILABLE_DIR+'/'+options['name']
        
        print options               
        print "Creating virtualhost: "+options['name']
        print "Folder: "+options['target_folder']
        
        if ( os.path.exists( options['target_folder'] ) == False ): 
            print "Folder "+options['target_folder']+" does not exist"        
            self._create_complete_path( options['target_folder'] )
            
        if ( os.path.exists( options['target_folder'] ) == False ):
            self.error( "Could not create target folder" ) #TODO fix this
            return False
                       
        if ( valid_domain_name( options['domain_name'] ) == False ):
            self.error ( 'Bad domain name: '+options['domain_name'] )
            return False
        
        if os.path.exists( complete_path ):
            raise "VhostExists", 'Virtual host already exists :('
            #self.error( 'Virtual host already exists :(' )
            return False        
        
        template = VHOST_TEMPLATE.replace( '||example||', options['domain_name'] )
        template = template.replace( '||target_folder||', options['target_folder'] )
        if ( options[ 'has_www' ] ):
            template = template.replace( '#ServerAlias www', 'ServerAlias www' )        
        
        self._write( complete_path, template )
          
        if ( options[ 'hack_hosts' ] ):
            self._command ('gksudo '+Configuration.APPPATH+'"/hosts-manager.py -a '+options['domain_name']+'"')
            if ( options[ 'has_www' ] ):
                self._command ('gksudo '+Configuration.APPPATH+'"/hosts-manager.py -a www.'+options['domain_name']+'"')
        self.changed = True        
        self.toggle( True ) #activate by default 
            
        return True
 
