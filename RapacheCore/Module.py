#!/usr/bin/env python

import sys
import os
import tempfile
import re
from RapacheCore import Configuration
from RapacheCore import Shell
from xml.dom.minidom import *

def is_denormalized_module ( fname ):
    try:   
        flink = os.readlink( Configuration.MODS_ENABLED_DIR +"/"+fname )
        flink = os.path.join(os.path.dirname( Configuration.MODS_AVAILABLE_DIR ), flink)                        
        #no exceptions ? Means it's a link
        return True
    except:
        return False
    return False
def is_not_normalizable( fname):
     dest = Configuration.MODS_AVAILABLE_DIR + "/" + fname
     return os.path.exists( dest )

def blacklisted ( fname ):
    if re.match( '.*[~]\s*$', fname ) != None : return True
    if re.match( '.*.swp$', fname ) != None : return True
    return False 
def normalize_module( fname ):
    print "Normalizing:", fname
    orig = Configuration.MODS_ENABLED_DIR + "/" + fname
    dest = Configuration.MODS_AVAILABLE_DIR + "/" + fname    
    if ( os.path.exists( dest ) == True ):
        print fname, "already exists in available dir. not even trying"
        return False
    command = 'gksudo "mv \''+orig+'\' \''+dest+'\'"'
    return Shell.command( command )
    return  os.path.exists( dest )
   
def get_module_dependants ( name, mods_dict ):
    dependants = []
    for idx in mods_dict:
        if idx != name:
            mod = mods_dict[ idx ]
            for dependancy in mod.data[ 'dependancies' ]:
                if dependancy == name: dependants.append( mod.data['name' ] )
    return dependants
"""
def module_list ():
    list = {}
    dirList=os.listdir( Configuration.MODS_AVAILABLE_DIR )
    dirList = [x for x in dirList if blacklisted( x ) == False ]
    for fname in  dirList :
        tokens = os.path.splitext( fname )
        if tokens[1] == '.load':
            mod = ModuleModel( tokens[0] )
            try:
                mod.load()
            except "VhostUnparsable":
                pass
            list[ fname ] = mod
            mod = None
    return list
"""
def module_list ():
    list = {}
 
    #load module descriptions
    module_descriptions = {}    
    f = open( Configuration.GLADEPATH + "/modules.xml" , "r")
    xml = f.read()
    f.close()
    document = parseString(xml)
    for node in document.getElementsByTagName("module"):
        name = node.getAttribute( "name" )
        if node.firstChild:
            description = node.firstChild.nodeValue
            module_descriptions[name] = description
 
    dirList=os.listdir( Configuration.MODS_AVAILABLE_DIR )
    dirList = [x for x in dirList if blacklisted( x ) == False ]
    for fname in  dirList :
        tokens = os.path.splitext( fname )
        if tokens[1] == '.load':
           description = None
           # find a description
 
           if module_descriptions.has_key(tokens[0]):
               description = module_descriptions[tokens[0]]
           elif module_descriptions.has_key("mod_" + tokens[0]):
               description = module_descriptions["mod_" + tokens[0]]
 
           mod = ModuleModel( tokens[0] )
           mod.data[ 'description' ] = description
           try:
                mod.load(  )
           except "VhostUnparsable":
               pass
           list[ fname ] = mod
           mod = None
    return list  
class ModuleModel:
    
    def __init__(self, name = None):
        self.defaults = {
            'enabled' : False
            , 'name' : None
            , 'domain_name': None
            , 'changed' : False        
            , 'dependancies' : []          
        }
        self.data = {}
        self.parsable = False
        self.changed = False
                
        self.data = self.defaults
        if ( name != None ):
            self.data[ 'name' ] = name
            self.data[ 'enabled' ] = self.is_enabled()

    def load (self, name = False):        
        try:
            #reset everything
            #print "Loading :\t",name
            if ( name == False ): name = self.data[ 'name' ]
            self.data = self.defaults   
            self.data['name'] = name
            
            
            #print "Loading(b) :\t",self.data[ 'name' ]            
            options = {}
            content = self.get_source()                
            self.__get_dependecies(content)
            self.parsable = True
        except:
            #print "Unparsable by me - unsupported"
            raise "ModuleUnparsable"
            return False
        self.data['configurable'] = \
                os.path.exists( os.path.join ( Configuration.MODS_AVAILABLE_DIR, self.data['name']+".conf" ))
            
        
        self.data.update( options )
        #print self.data
        return True
    def __get_dependecies(self, content):   
        content = content.split("\n")
        dependancies = []
        for line in content:
            match = re.match ( r'# Depends:(.*)', line )
            if match != None:                                 
                dependancy = match.groups()[0].strip()
                if dependancy != "" : dependancies.append( dependancy )
        self.data[ 'dependancies' ] = dependancies
    def is_enabled ( self ):
        orig = self.data[ 'name' ] + ".load"              
        dirList=os.listdir(  Configuration.MODS_ENABLED_DIR )        
        for fname in dirList:
            try:                                
                flink = os.readlink( Configuration.MODS_ENABLED_DIR +"/"+fname )               
                flink = os.path.join(os.path.dirname( Configuration.MODS_ENABLED_DIR +"/" ), flink)
                #please note debian brilliantly features a nice set of
                # mixed absolute and relative links. FREAKS !
                # the added "/" is also necessary
                flink = os.path.normpath(flink)               
                if ( flink == Configuration.MODS_AVAILABLE_DIR+"/"+orig ):
                    return True
            except:
                pass
          
        return False
    
    def _write(self, complete_path, content ):    
        tempfilename = tempfile.mktemp()
        print "creating temporary file "+tempfilename
        logfile = open( tempfilename , 'w')
        logfile.write( content )
        logfile.close()
        command = "gksudo cp "+tempfilename+" "+complete_path
        print "copying tempfile in the appropriate location: "+command
        Shell.command( command )
    
    def toggle( self, status ):
        "status = True|False"
        if status:
            command = "a2enmod"
        else :
            command = "a2dismod"        
        # set new value
        #tokens = self.data['name'].split('.')
        #del tokens[ len( tokens ) -1 ]
        #name = ".".join(tokens)
        name = self.data['name']
        command = "gksudo "+command+" "+name
        Shell.command( command )
        self.data['enabled'] = self.is_enabled()
        self.changed = True
    """ NOT FOR NOW    
    def delete( self ):
        "Deletes a VirtualHost configuration file"
        if ( self.is_enabled() ): self.toggle( False )
        Shell.command( 'gksudo rm '+Configuration.MODS_AVAILABLE_DIR+'/'+self.data['name'] )
    """
     
    def get_source ( self ):
        file = open( Configuration.MODS_AVAILABLE_DIR+'/'+self.data['name']+".load", 'r' )
        content = file.read()
        file.close()
        return content
    def get_configuration ( self ):
        file = open( Configuration.MODS_AVAILABLE_DIR+'/'+self.data['name']+".conf", 'r' )
        content = file.read()
        file.close()
        return content
    def save_configuration (self, content):
        complete_path = file = Configuration.MODS_AVAILABLE_DIR+'/'+self.data['name']+".conf"
        self._write(complete_path, content)