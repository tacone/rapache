#!/usr/bin/env python

import getopt, sys
import os
import re
import subprocess
"""
Things to remember:
    - if 2 equal domain names are found in /etc/hosts the first wins
"""

# Flow:
# ------------
# hosts-manager -a example.loc 10.0.0.1
#
# example.loc exists ?
#   No. Add it at the end of file
#   Yes
#       is ip the same ?
#           yes. Skipping.
#           no.
#               remove domain name from the line it first appears in
#               if the line contained only one domain, remove the line altogheter
#               add a new line just below $IP    $DOMAIN_NAME


#IPv4 REGEXP: \d{1,3}\.\d{1,3}\.\d{1,3}'
#IPv4 (2): \b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b
#SOSTITUZIONE: re.sub( r'(\s)(www.mu.loc)(\s|$)', r'\3\1xxx\3', subject )
#CAMBIO IP:


#TODO: regexp the crap out of IP's (v4 and v6)
#TODO: strip in-line comments 127.0.0.1 domain.localhost #strip-this.com

class HostsManager:
    SUDO = "sudo"
    HOSTS = "/etc/hosts"
    REGEXP_IPV4 = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    opts = None
    def __init__( self, console = False ):
        if ( console ):

            try:
                opts, args = getopt.getopt(sys.argv[1:], "ho:v:ar", ["help", "output="])
                self.opts = opts
                self.args = args
            except getopt.GetoptError, err:
                # print help information and exit:
                print str(err) # will print something like "option -a not recognized"
                self.usage()
                sys.exit(2)
            output = None
            verbose = False
            if len(opts) == 0:
                self.usage()
                exit()
            for o, a in opts:
                if o == "-v":
                    verbose = True
                elif o == "-a":                                        
                    if ( len( args ) == 0 ):                        
                        self.usage()
                        sys.exit()
                    self.create( *args )
                elif o == "-r":
                    if ( len( args ) == 0 ):
                        self.usage()
                        sys.exit()
                    self.remove( *args )                    
                elif o in ("-h", "--help"):
                    self.usage()
                    sys.exit()
                elif o in ("-o", "--output"):
                    output = a
                    print args
                else:
                    assert False, "unhandled option"
    def strip_domain ( self, line, domain_name ):
        domain_regexp = domain_name.replace( '.', '\\.' ) #quote for regexp
        regexp_just_1_domain = r'^\s*('+self.REGEXP_IPV4+')(\s*)('+domain_regexp+')(\s|$)'
        if( re.search( regexp_just_1_domain , line, re.IGNORECASE ) ):
            return False           
        tokens = re.split( r'(\s*)', line )
        new_tokens = []
        changed = False
        for word in tokens:                                                    
            if ( word.strip().lower() != domain_name.strip().lower() ):                  
                if ( changed == True and new_tokens[-1] == ' ' and word == ' ' ):
                    """ nothing """               
                else:
                    new_tokens.append( word )                    
                changed = False                                                      
            else:
                changed = True        
        line = "".join( new_tokens )
        return line
    def _security_check ( self, domain_name, ip ):
        if ( re.search( '^localhost$', domain_name, re.IGNORECASE )!=None ):
            print "hosts-manager won't operate localhost. So sorry"
            return False
        p = subprocess.Popen("hostname", stdout=subprocess.PIPE)
        hostname = p.communicate()[0]
        hostname = hostname.replace( "\n", "" )
        if ( re.search( '^'+hostname+'$', domain_name, re.IGNORECASE )!=None ):
            print "The domain name you gave corresponds to local computer's host name. I won't touch it, sorry"
            return False
        if ( ip != False ):
            if ( re.search( '^'+self.REGEXP_IPV4, ip ) == None ):
                print ip+" is a bad IP"
                return False
        return True
    def _normalize_ip ( self, ip ):
        if ( ip == None ): ip="127.0.0.1"
        if ( re.search( '^localhost$', ip, re.IGNORECASE )!=None ):
            ip="127.0.0.1"
        return ip    
    def remove ( self, domain_name ):                
        if self._security_check( domain_name, False ) == False: return False
        content = self._get_content()
        found = self._find_domain( content, domain_name, False )
        #   self.strip_domain ( found['line'], domain_name )    
        if found == False: 
            print 'Domain "'+domain_name+'" not found'
            return True        
        content[ found['idx'] ]  = self.strip_domain ( found['line'], domain_name )                                                                                                      
        if content[ found['idx'] ] == False:
            #content[ found['idx'] ] = "xxxxxxxxxxxxxxxxx"
            del content[ found['idx'] ]        
        self._write( content )
        
    def find (self, domain_name, ip = None ):    
        ip = self._normalize_ip( ip )
        if self._security_check( domain_name, ip ) == False: return False
        content = self._get_content()
        found = self._find_domain( content, domain_name, ip )
        return found
        
    def create( self, domain_name, ip = None ):      
        ip = self._normalize_ip( ip )
        if self._security_check( domain_name, ip ) == False: return False
        content = self._get_content()
        found = self._find_domain( content, domain_name, ip )
        if ( found == False ):           
            print "adding "+ip+" "+domain_name+" at the end of file"
            content.append( ip+"\t"+domain_name+"\n" )
        else:        
            print "Found "+domain_name+" at line "+str(found['idx']+1)                        

            print "Found domain: "+found['domain']+" ("+found['ip']+")"
            #print domain_regexp       
            if ( found['domain'].lower() == domain_name.lower()):
                if ( ip == found['ip'] ):       
                    print ">>>"+found['line']+"Definition already present, skipping"
                    return True
                else:                       
                    print ">>>"+found['line']
                    print "Ip differs. "+found['ip']+" has to become "+ip
                    print "Removing domain name from this line"
                    print "Creating a new entry in the next line"                        
                    content[ found['idx'] ]  = self.strip_domain ( found['line'], domain_name )                                                                                              
                    content[ found['idx']+1: 1 ] = [ ip+"\t"+domain_name+"\n" ]
                    if content[ found['idx'] ] == False:
                        content.remove( False )                    
                    return True
            else:
                print ">>>"+line
                print "Replacing "+domain_name+" at line "+str(found['idx']+1)
                return True
                
        
                                 
        self._write( content )
    
    def _get_content ( self ):
        file = open( '/etc/hosts', 'r' )
        content =  file.readlines()
        file.close()
        return content
    def _find_domain( self, content, domain_name, ip = None ):  

        output = []        
        domain_regexp = domain_name.replace( '.', '\\.' ) #quote for regexp        
        found = False
        # print domain_regexp
        
        for idx, line in enumerate( content ):            
            regexp =     r'^\s*('+self.REGEXP_IPV4+')\s*.*(\s*)('+domain_regexp+')(\s|$)'
            match = re.search( regexp , line, re.IGNORECASE )                
            if ( match != None ): 
                print "Found "+domain_name+" at line "+str(idx+1)
                found = True                
                found_entry = match.groups()                          
                found_ip = found_entry[0]
                found_domain = found_entry[2]
                print "Found domain: "+found_domain+" ("+found_ip+")"
                #print domain_regexp       
                if ( found_domain.lower() == domain_name.lower()):
                    result = { 
                        'domain':found_domain
                        , 'ip':found_ip
                        , 'idx': idx
                        , 'line': line }
                    
                    return result
        return False
    def _create( self, domain_name, ip = None ):  
    
        ip = self._normalize_ip( ip )
        if self._security_check( domain_name, ip ) == False: return False      
        
        return self._find_domain ( domain_name, ip )
        
        file = open( '/etc/hosts', 'r' )
        content =  file.readlines()
        file.close()
        
        output = []        
        domain_regexp = domain_name.replace( '.', '\\.' ) #quote for regexp        
        found = False
        # print domain_regexp
        
        for idx, line in enumerate( content ):            
            regexp =     r'^\s*('+self.REGEXP_IPV4+')\s*.*(\s*)('+domain_regexp+')(\s|$)'
            match = re.search( regexp , line, re.IGNORECASE )                
            if ( match != None ): 
                print "Found "+domain_name+" at line "+str(idx+1)
                found = True                
                found_entry = match.groups()                          
                found_ip = found_entry[0]
                found_domain = found_entry[2]
                print "Found domain: "+found_domain+" ("+found_ip+")"
                #print domain_regexp       
                if ( found_domain.lower() == domain_name.lower()):
                    if ( ip == found_ip ):       
                        print ">>>"+line+"Definition already present, skipping"
                        break
                    else:                       
                        print ">>>"+line
                        print "Ip differs. "+found_ip+" has to become "+ip
                        print "Removing domain name from this line"
                        print "Creating a new entry in the next line"                        
                        content[ idx ]  = self.strip_domain ( line, domain_name )                                                                                              
                        content[ idx+1: 1 ] = [ ip+"\t"+domain_name+"\n" ]
                        if content[ idx ] == False:
                            content.remove( False )
                        
                        break
                else:
                    print ">>>"+line
                    print "Replacing "+domain_name+" at line "+str(idx+1)
                    break
        if ( found == False ):           
            print "adding "+ip+" "+domain_name+" at the end of file"
            content.append( ip+"\t"+domain_name+"\n" )
                                 
        self._write( content )
    def _write ( self, content ):
        if ( 0 ): #debug. output without writing to disk
            for idx, line in enumerate( content ): 
                print str(idx)+". "+line.replace("\n", '')
        else:
            try:
                dest = open( '/etc/hosts', 'w' )
                dest.writelines( content )
                dest.close()
            except:
                print "Error writing to file. Do you have the needed permissions?"
    def _system_output ( command ):
        1
    def _get_opt ():
        print 1
    def usage ( self ):
        print """Hosts manager v. 0.1
USAGE: hosts-manager.py -a hostname [ip]
       hosts-manager.py -r hostname [ip]

Options:
   -a create a new entry in /etc/hosts
   -r remove an entry in /etc/hosts       
"""
    

if __name__ == "__main__":
    HostsManager( True )
