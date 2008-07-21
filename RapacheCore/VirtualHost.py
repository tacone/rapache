#!/usr/bin/env python

import sys
import os
import tempfile
import re
from RapacheCore import Configuration
from RapacheCore.ApacheConf import *
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
        flink = os.readlink( Configuration.SITES_ENABLED_DIR +"/"+fname )
        flink = os.path.join(os.path.dirname( Configuration.SITES_AVAILABLE_DIR ), flink)                        
        #no exceptions ? Means it's a link
        return True
    except:
        return False
    return False
def is_not_normalizable( fname):
     dest = Configuration.SITES_AVAILABLE_DIR + "/" + fname
     return os.path.exists( dest )
 
def normalize_vhost( fname ):
    print "Normalizing:", fname
    orig = Configuration.SITES_ENABLED_DIR + "/" + fname
    dest = Configuration.SITES_AVAILABLE_DIR + "/" + fname    
    if ( os.path.exists( dest ) == True ):
        print fname, "already exists in available dir. not even trying"
        return False
    command = 'gksudo "mv \''+orig+'\' \''+dest+'\'"'
    return Shell.command( command )
    return  os.path.exists( dest )
    
class VirtualHostModel:
    
    def __init__(self, name = None):
        self.defaults = {
            'enabled' : False
            , 'name' : None
            , 'ServerName': None
            , 'changed' : False            
            , 'hack_hosts' : False
            , 'DocumentRoot' : None            
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
                    return match            
        return False
    
    def _get_conf_value(self, content, regexp):        
        match = self._search(content, regexp )
        if ( match == False or match == None ): return None
        found_entry = match.groups()                          
        found_value = found_entry[0]
        return found_value
    def load(self, name = False, plugin_manager = None):
    	if ( name == False ): name = self.data[ 'name' ]
    	options = {}    	
        parser = Parser()
        parser.load(  os.path.join(Configuration.SITES_AVAILABLE_DIR, name) )
        try:
            piece = VhostParser( parser )
        except "VhostNotFound":
         	self.parsable = False
         	return False
        domain_name = piece.get_value( 'ServerName' )
        if domain_name == None:
         	self.parsable = False
         	#return False
        options[ 'ServerName' ] = domain_name
        options[ 'ServerAlias' ] = piece.get_options( 'ServerAlias' )
        print options[ 'ServerAlias' ]
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
            
        
    def loaad (self, name = False):
        print "Loading Vhosts list"
        try:
            #reset everything
            #print "Loading :\t",name
            if ( name == False ): name = self.data[ 'name' ]
            self.data = self.defaults   
            self.data['name'] = name
            
            #print "Loading(b) :\t",self.data[ 'name' ]            
            options = {}
            content = self.get_source()        
            #domain_name = self._get_domain_name(content)
            domain_regexp = r'^\s*ServerName\s+([A-Za-z0-9.\-_]*)'
            domain_name = self._get_conf_value(content, domain_regexp)
            options[ 'ServerName' ] = domain_name
            domain_regexp = domain_name.replace( '.', '\\.' ) #quote for regexp
            www_regexp = r'^\s*ServerAlias\s*[^#]*\s+www\.'+domain_regexp+'(\s*|$)'
            folder_regexp = domain_regexp = r'^\s*DocumentRoot\s+(\S+\s*\S+)'
            
            #print "Domain Name :\t"+domain_name             
            if self._search(content, www_regexp ) != None \
            and self._search(content, www_regexp ) != False  :
                options[ 'has_www' ] = True
            else:
                options[ 'has_www' ] = False 
    
            #print "Has www :\t"+str(options[ 'has_www' ])
                
            options[ 'DocumentRoot' ] = self._get_conf_value(content, folder_regexp)
            
            #print "Document Root :\t"+str( options[ 'DocumentRoot' ] )
            hosts = HostsManager()
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
        #print self.data
        return True
        
    def is_enabled ( self ):
        orig = self.data[ 'name' ]        
        dirList=os.listdir(  Configuration.SITES_ENABLED_DIR )
        for fname in dirList:
            try:                                
                flink = os.readlink( Configuration.SITES_ENABLED_DIR +"/"+fname )               
                flink = os.path.join(os.path.dirname( Configuration.SITES_ENABLED_DIR +"/" ), flink)
                # please note debian features a nice set of
                # mixed absolute and relative links. FREAKS !
                # the added "/" is also necessary
                flink = os.path.normpath(flink)               
                if ( flink == Configuration.SITES_AVAILABLE_DIR+"/"+orig ):
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
        command = "gksudo "+command+" "+self.data['name']
        if self.simulation:
            print "SIMULATED "+command
            self.data['enabled'] = status
        else:
            Shell.command( command )
            self.data['enabled'] = self.is_enabled()
        self.changed = True
        
    def delete( self ):
        "Deletes a VirtualHost configuration file"
        if ( self.is_enabled() ): self.toggle( False )
        Shell.command( 'gksudo rm '+Configuration.SITES_AVAILABLE_DIR+'/'+self.data['name'] )
    def _create_complete_path ( self, complete_path ):
        print "Attempting to create: " + complete_path
        tokens = complete_path.split( '/' )
        del tokens[ 0 ]        
        path = ''
        for piece in tokens:
            path = path + '/' + piece
            if ( os.path.exists( path ) == False ):
                try:
                    Shell.command( 'gksudo "mkdir '+path+'"' )
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
        parser.load(  Configuration.SITES_AVAILABLE_DIR+'/'+name )
        piece = VhostParser( parser )
        old_servername = piece.get_value( 'ServerName' )
        
        # Get a bit more dynamic with it
        for key in new_options.keys():
        	obj = new_options[key]
        	if isinstance(obj, list):
        		piece.set_value(key, '')
			for opt in obj:
            			piece.add_option(key, opt )
		elif isinstance(obj, str):
        		 piece.set_value(key, obj)
        
        #piece.set_value('ServerAlias',  '' )
        #for domain in new_options ['ServerAlias']:
        #    piece.add_option('ServerAlias', domain )
                                        
        print "DocumentRoot From",piece.get_value('DocumentRoot' ),"to",new_options['DocumentRoot']
        piece.set_value('DocumentRoot', new_options['DocumentRoot'] )
                
        print "ServerName From",piece.get_value('ServerName' ),"to",new_options['ServerName']
        piece.set_value('ServerName', new_options['ServerName'] )                
        complete_path = Configuration.SITES_AVAILABLE_DIR+'/'+ name 
        
        print "Writing.."
        print parser.get_source()
        self._write( complete_path, parser.get_source() )
        
        #if the servername coincides with the configuration filename
        #we try to stick with the convention
        new_name = Configuration.SITES_AVAILABLE_DIR + "/"+ new_options['ServerName']
        old_name = Configuration.SITES_AVAILABLE_DIR + "/"+ old_servername
        print "old name", old_name
        print "new name", new_name
        
        if old_name != new_name and os.path.exists( new_name ) == False:
            print "Server name changed, updating conf filename"
            self.toggle( False )     
            Shell.command( 'gksudo mv "'+old_name+'" "'+new_name+'"' )
            if os.path.exists( new_name ) == True:
                #success ! we need to reload vhost with the new name
                self.load( new_options['ServerName'] )
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
        Shell.command( command )
        
        
    def create ( self, new_options ):                
        
        options = self.data
        options.update( new_options )        
        
        #as of creation-time name is not expected to be in options
        options['name'] = options[ 'ServerName' ]
        complete_path = Configuration.SITES_AVAILABLE_DIR+'/'+options['name']
        
        print options               
        print "Creating virtualhost: "+options['name']
        print "Folder: "+options['DocumentRoot']
        
        if ( os.path.exists( options['DocumentRoot'] ) == False ): 
            print "Folder "+options['DocumentRoot']+" does not exist"        
            self._create_complete_path( options['DocumentRoot'] )
            
        if ( os.path.exists( options['DocumentRoot'] ) == False ):
            self.error( "Could not create target folder" ) #TODO fix this
            return False
                       
        if ( valid_domain_name( options['ServerName'] ) == False ):
            self.error ( 'Bad domain name: '+options['ServerName'] )
            return False
        
        if os.path.exists( complete_path ):
            raise "VhostExists", 'Virtual host already exists :('
            #self.error( 'Virtual host already exists :(' )
            return False        
        """
        template = VHOST_TEMPLATE.replace( '||example||', options['ServerName'] )
        template = template.replace( '||DocumentRoot||', options['DocumentRoot'] )
        if ( options[ 'has_www' ] ):
            template = template.replace( '#ServerAlias www', 'ServerAlias www' )        
        """
        parser = Parser()
        parser.set_content_from_string( VHOST_TEMPLATE )
        piece = VhostParser( parser )
        piece.set_value('ServerName',  options['ServerName'] ) 
        piece.set_value('DocumentRoot',  options['DocumentRoot'] ) 

        print "min", piece.min, "max", piece.max
        #reset previous aliases
        piece.set_value('ServerAlias',  '' )
        for domain in options ['ServerAlias']:
            piece.add_option('ServerAlias', domain )
        print parser.get_content()
            
        self._write( complete_path, "\n".join(parser.get_content() ) )
          
        if ( options[ 'hack_hosts' ] ):
            Shell.command ('gksudo "'+Configuration.APPPATH+'/hosts-manager -a '+options['ServerName']+'"')
            for alias_name in options[ 'ServerAlias' ]:
            	Shell.command ('gksudo "'+Configuration.APPPATH+'/hosts-manager -a '+alias_name+'"')
        self.changed = True        
        self.toggle( True ) #activate by default 
            
        return True
