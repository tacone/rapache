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
import unittest
import sys
sys.path.append('../RapacheCore')
from ApacheParser import *
import re

class LineParserTest( unittest.TestCase ):
    def old_directive (self):
        line = Line( '\t\t\nDocumentRoot /var/www' )
        self.assertEquals( line.directive, 'DocumentRoot' )

#TODO: test newlines !! strip them !
#TODO: raise exception on unexpected close tags !

#allow to reuse ApacheConfTest.py
def Parser():
    return ApacheParser()
 
STRING_VHOST = """#this won't work in apache because it misses some
# <TAGS>. just for testing options
    ServerName bart.loc
    ServerAlias www.bart.loc test.bart.loc
    DocumentRoot /var/www/bart.loc/httpdocs/html
    Options Indexes FollowSymLinks MultiViews
    LogLevel    debug
    ServerAdmin    webmaster@bart.loc
    ServerSignature    off
    ErrorDocument 500 "Sorry I can't wrap my head around it"
    NoOptions
# let the file end with this line, don't add empty newlines or tests will fail"""
    
class ApacheParserTest ( unittest.TestCase ):
    apache2conf = 'datafiles/apache2.conf'
    apache2conf_expected  = {
     'Group': '${APACHE_RUN_GROUP}',
     #'StartServers': '2',
     #'ThreadsPerChild': '25',
     'HostnameLookups': 'Off',
     'LockFile': '/var/lock/apache2/accept.lock',
     'KeepAlive': 'On',
     'Include': '/etc/apache2/sites-enabled/',
     'ServerRoot': '/etc/apache2',
     #'MinSpareServers': '5',
     #'MinSpareThreads': '25',
     #'MaxClients': '150',
     'User': '${APACHE_RUN_USER}',
     #'MaxRequestsPerChild': '0',
     #'Deny': 'from all',
     'ServerSignature': 'On',
     'Timeout': '300',
     'KeepAliveTimeout': '15',
     'AccessFileName': '.htaccess',
     #'Order': 'allow,deny',
     #'MaxSpareServers': '10',
     'ServerTokens': 'Full',
     'ErrorLog': '/var/log/apache2/error.log',
     'LogLevel': 'warn',
     'LogFormat': '#ERROR',
     #'MaxSpareThreads': '75',
     'MaxKeepAliveRequests': '100',
     'DefaultType': 'text/plain',
     'PidFile': '${APACHE_PID_FILE}'
    }
    optionsconf = 'datafiles/options.conf'
    vhostconf = 'datafiles/vhost.conf'
    fromtemplateconf = 'datafiles/fromtemplate.conf'
    defaultssl = 'datafiles/default-ssl'
    valid_tags = {
        '<VirtualHost *>' : ('VirtualHost', '*')
      , '<Directory "/usr/share/doc/">': ('Directory', '/usr/share/doc/')
      , '<IfModule mpm_prefork_module>': ('IfModule', 'mpm_prefork_module')
      , '<LocationMatch .*/music/stream.php>': ('LocationMatch', '.*/music/stream.php')
      , '<Tag>': ('Tag', None )
    }
    invalid_tags = [
        'ErrorLog /var/log/apache2/error.log'
      , '#    <LocationMatch .*/pl/stream/[0-9]+/[0-9]+>'
    ]
    
    def test_load(self):
        p = ApacheParser()
        p.load( self.apache2conf )
        self.assertTrue( p.linescount() > 0 )
        #p.dump_xml()
    def test_get_value(self):
        p = Parser()
        p.load( self.apache2conf )
        
        for key in self.apache2conf_expected :
            expected = self.apache2conf_expected[ key ]
            if expected == '#ERROR':
                print "Please cover parsing of ",key," in apache2.conf with tests"
            else:
                self.assertEqual( p.get_value( key ), expected )
        #cool, let's try to get a non-existant directive
        expected = None
        key = 'IDontExist'
        self.assertEqual( p.get_value( key ), expected )
    def test_set_value (self):
        p = Parser()
        p.load( self.apache2conf )
        length = p.linescount()
        
        for key in self.apache2conf_expected:
            self.assertFalse( p.is_modified( key ))
        
        for key in self.apache2conf_expected :
            if self.apache2conf_expected[ key ] == '#ERROR':
                print "Please cover parsing of ",key," in apache2.conf with tests"
            else:
                p.set_value( key, 'NULLIFIED' )
        #number of lines shuoldn't be changed
        self.assertEqual( p.linescount(), length )
        dict = p.dump_values()
        
        for key in dict: 
            #print key,dict[key]
            #print key,"-->",dict[key]
            res = self.assertTrue(dict[ key ]=='NULLIFIED' or dict[ key ]=='#ERROR' )
            if dict[ key ]=='NULLIFIED':
                self.assertTrue( p.is_modified( key ))
            else:
                self.assertFalse( p.is_modified( key ))
                
        p.set_value( 'DocumentRoot', '/var/www/htdocs' )
        #DocumentRoot is not present in the file, should add a new line
        self.assertEqual( p.linescount(), length +1 )
        #try setting a value with spaces
        p.set_value( 'DocumentRoot', '/var/www/my htdocs' )
        #length should be the same as before
        self.assertEqual( p.linescount(), length +1 )        
        self.assertEqual( p.get_value( 'DocumentRoot' ), '/var/www/my htdocs' )
    def test_remove_value (self):
        p = Parser()
        p.load( self.optionsconf )
        length = p.linescount()
        res = p.remove_value( 'Options' );
        self.assertTrue( res )
        self.assertEqual( length -1, p.linescount() )
        #Options shouldn't exist anymore
        length = p.linescount()
        res = p.remove_value( 'Options' );
        self.assertFalse( res )
        self.assertEqual( length, p.linescount() )
        #this directive doesn't exists
        res = p.remove_value( 'Doesntexist' );
        self.assertFalse( res )
        self.assertEqual( length, p.linescount() )
        
        
        
        p = Parser()
        p.set_content_from_string( """    ServerName bart.loc
    ServerAlias www.bart.loc test.bart.loc
    DocumentRoot /var/www/bart.loc/httpdocs/html
    Options Indexes FollowSymLinks MultiViews
    LogLevel    debug
    ServerAdmin    webmaster@bart.loc
    ServerSignature    off
    ErrorDocument 500 "Sorry I can't wrap my head around it"
    NoOptions""" )
        #removing the first directive
        length = p.linescount()
        res = p.remove_value( 'ServerName' );
        self.assertTrue( res )
        self.assertEqual( length -1, p.linescount() )
        #removing the last
        length = p.linescount()
        res = p.remove_value( 'NoOptions' );
        self.assertTrue( res )
        self.assertEqual( length -1, p.linescount() )
        
    def test_has_option(self):
        p = Parser()
        p.load( self.optionsconf )
        self.assertTrue( p.has_option( 'ServerAlias', 'www.bart.loc' ) )
        self.assertTrue( p.has_option( 'ServerAlias', 'test.bart.loc' ) )
        self.assertFalse( p.has_option( 'ServerAlias', 'notex.bart.loc' ) )
        self.assertFalse( p.has_option( 'ServerAlias', '' ) )
        self.assertFalse( p.has_option( 'ServerAlias', None ) )
        self.assertFalse( p.has_option( 'ServerAlias', True ) )
    def test_get_options(self):
        p = Parser()
        p.load( self.optionsconf )
        expected = ['www.bart.loc', 'test.bart.loc']
        options = p.get_options( 'ServerAlias' )
        self.assertEqual( options, expected )
        self.assertEqual( p.get_options( 'NoOptions' ), [] )
    def test_get_directive (self):
        p = Parser()
        p.load( self.apache2conf )
        for key in self.apache2conf_expected :
            expected = self.apache2conf_expected[ key ]
            if expected == '#ERROR':
                print "Please cover parsing of ",key," in apache2.conf with tests"
            else:
                self.assertNotEquals ( p.get_directive(key).find(key), -1 )
                self.assertNotEquals ( p.get_directive(key).find(expected), -1 )
        
    def test_set_directive (self):
        p = Parser()
        p.load( self.apache2conf )
        length = p.linescount()
        
        p.set_directive( "KeepAliveTimeout", "\t\tKeepAliveTimeout 30" )
        self.assertEqual( length, p.linescount() )
        self.assertEqual( p.get_value( 'KeepAliveTimeout' ), "30" )
        
        p.set_directive( "NewDirective", "\t\tNewDirective MyValue" )
        self.assertEqual( p.get_value( 'NewDirective' ), 'MyValue' )
        self.assertEqual( length +1 , p.linescount() )
        
    def test_add_option(self):
        p = Parser()
        p.load( self.optionsconf )
        expected = ['www.bart.loc', 'test.bart.loc', 'new.bart.loc' ]
        self.assertFalse( p.is_modified( 'ServerAlias' ))
        p.add_option( 'ServerAlias', 'new.bart.loc' )
        self.assertTrue( p.is_modified( 'ServerAlias' ))
        options = p.get_options( 'ServerAlias' )
        self.assertEqual( options, expected )
        
        self.assertEqual( p.get_options( 'NoOptions' ), [] ) 
        self.assertFalse( p.is_modified( 'NoOptions' ))
        p.add_option( 'NoOptions', 'MoreFunnyNow' )
        self.assertTrue( p.is_modified( 'NoOptions' ))
        self.assertEqual( p.get_options( 'NoOptions' ), ['MoreFunnyNow'] ) 
        p.add_option( 'NoOptions', 'AndEvenMore' )
        self.assertEqual( p.get_options( 'NoOptions' ), ['MoreFunnyNow','AndEvenMore'] ) 
        
        #TODO: fix this
        """expected = ['500', 'Sorry I can\'t wrap my head around it']
        options = p.get_options( 'ErrorDocument' )
        self.assertEqual( p.get_value( 'ErrorDocument' ), 1 )
        self.assertEqual( options, expected )"""
        
        #testing adding to an empty directive
        p = Parser()
        p.set_content_from_string( "\t\tServerAlias" )
        p.add_option( 'ServerAlias', 'www.example.net' )
        self.assertEqual( p.get_options( 'ServerAlias' ), ['www.example.net'] )
        
    def test_remove_option(self):
        p = Parser()
        p.load( self.optionsconf )
        expected = ['www.bart.loc', 'test.bart.loc', 'new.bart.loc' ]
        p.remove_option( 'ServerAlias', 'new.bart.loc' )
        
        options = p.get_options( 'ServerAlias' )
        
    def test_get_content(self):
        p = Parser()
        p.load( self.optionsconf )
        content = p.get_content()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13 )
        #do lines contain extra  trailing \n ?
        self.assertEqual( len( "/n".join( content ).split( "\n" )), 13 )
        
        p.set_value( 'DocumentRoot', '/var/www/fake' )
        content = p.get_content()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13 )
        
        p.set_value( 'NotYetExistant', 'value' )
        content = p.get_content()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13+1 )
        
        p.add_option( 'NewOption', 'option1' )
        content = p.get_content()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13+2 )
        
        p.add_option( 'NewOption', 'option2' )
        content = p.get_content()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13+2 )
        
        
        
    def test_get_source (self):
        p = Parser()
        p.load( self.optionsconf )
        source = p.get_source()
        #let's make sure we suppresed newline-spam with hate
        content = source.split( "\n" )
        self.assertEqual( len( content), 13 )
    def test_set_content_from_string (self):
        p = Parser()
        p.set_content_from_string( STRING_VHOST )
        content = p.get_content()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 12 )
        #do lines contain extra  trailing \n ?
        joinedcontent = "".join( content )
        content_line_number = len( joinedcontent.split( "\n" ) )
        self.assertEqual( content_line_number, 12 )
    def test_is_tag_open(self):
        p = Parser()
        for line in self.valid_tags:
            result = p.is_tag_open( line )
            expected = self.valid_tags[line]
            self.assertEquals( result, expected )
        for line in self.invalid_tags:
            result = p.is_tag_open( line )
            self.assertFalse( result )
    def test_nesting (self):   
        p = Parser()
        p.load( self.vhostconf )
        #p.dump_xml( True )
        self.assertEqual( p.linescount(), 3)
    def test_get_virtualhost(self):
        #testing not existing virtualhost
        p = Parser()
        p.load( self.optionsconf )
        try:
            vhost = p.get_virtualhost()
            self.assertFalse( True )
        except VhostNotFound:
            pass
            
        #testing existing virtualhost
        p = Parser()
        p.load( self.vhostconf )
        #p.dump_xml( True )
        vhost = p.get_virtualhost()
        self.assertTrue( isinstance( vhost, SubTag ))
        self.assertEqual( len( vhost.get_content() ), 13+3 )
        
        #testing a virtualhost nested into a <ifmodule>
        p = Parser()
        p.load( self.defaultssl )
        #p.dump_xml( True )
        v = p.get_virtualhost()
        
    def test_get_content_with_nesting(self):
        """tests that the content of subtags is actually rendered in
        the parent element get_content()"""
        file = open ( self.vhostconf, 'r' )
        original_content = file.readlines()
        file.close()
        
        p = Parser()
        p.load( self.vhostconf )
        content = p.get_content()        

        #    print "\n".join( content )
        self.assertEqual( type(content), type([]) )
        #do lines contain extra  trailing \n ?
        self.assertEqual( len(original_content), len(content) )
        for idx, value in enumerate( original_content ):
            #note rstrip(), we don't preserve trailing spaces yet
            self.assertEqual( original_content[ idx ].rstrip(), content[ idx].rstrip() )
            #self.assertEqual( original_content, content )
    
    def test_nesting_scope_of_operations(self):
        p = Parser()
        p.load( self.vhostconf )
        #p.dump_xml( True )
        vhost = p.get_virtualhost()
        expectedlen = 16
        self.assertTrue( isinstance( vhost, SubTag ))
        self.assertEqual( len( vhost.get_content() ), expectedlen )
        #this is inside <virtualhost>
        self.assertEqual( vhost.get_value( 'ServerName'), 'bart.loc' )
        #subtags directives should not be accessible
        self.assertEqual( vhost.get_value( 'options'), None )
        #inside the virtualhost but placed after a subtag. should work
        self.assertEqual( vhost.get_value( 'ServerSignature'), "off" )
        #outside the <virtualhost>.. NEIN !
        self.assertEqual( vhost.get_value( 'OuterDirectives'), None )
    def test_newlines_on_the_last_line(self):
        p = Parser()
        p.load( self.vhostconf )
        #p.dump_xml( True )
        vhost = p.get_virtualhost()
        expectedlen = 16
        self.assertEqual( len( vhost.get_content() ), expectedlen )
        vhost.add_option( 'newoption', 'opt1' )
        self.assertEqual( len( vhost.get_content() ), expectedlen +1 )
    def test_newlines_on_get_source(self):
        """yet another test on newlines reliability"""
        print "====== test_newlines_on_get_source ======="
        p = Parser()
        p.load( self.fromtemplateconf )
        actuallen = len( p.get_source().split("\n" ) );
        self.assertNotEqual( actuallen, 1 )
        vhost = p.get_virtualhost()
        vhost.set_value( 'DocumentRoot', '/var/www/bbb/httpdocs' )
        vhost.set_value( 'ServerName', 'bbba' )
        vhost.add_option( 'ServerAlias', 'www.bbba' )
        self.assertEqual( actuallen, len( p.get_content() ) )        
        
        source = p.get_source()
        self.assertEqual( actuallen, len( source.split("\n")) )
        for count in range( 1, 6 ):
            expectedlen = len( source.split("\n") )
            p = Parser()
            try:
                p.set_content_from_string( source )
            except:
                print "ERROR on this source, at iteration %s" % str(count)
                print source
                print "--------------------"
            source = p.get_source()
            actlen = len(source.split("\n"))
            try:
                self.assertEqual( expectedlen, actlen )
            except:
                print "-------------YYYY--------------____"
                print "test_newlines_on_get_source failed at iteration:", count
                print "exp: %s, actual count: %s" % (str(expectedlen), str(actlen))
                #print "-----> source dump"
                #print p.get_source()
                #print "-----> end source dump"
    def test_virtualhost_get_port(self):
        p = Parser()
        p.load( self.fromtemplateconf )
        v = p.get_virtualhost()
        self.assertEqual( v.get_port(), None )        
        p = Parser()
        p.load( self.defaultssl )
        v = p.get_virtualhost()        
        self.assertEqual( v.get_port(), 443 )
        
    def test_virtualhost_ports(self):
        p = Parser()
        p.load( self.fromtemplateconf )                  
        v = p.get_virtualhost()        
        self.assertEqual( v.get_port(), None )
        v.set_port( 80 )
        self.assertEqual( v.get_port(), 80 )
        
        source = p.get_source()
        basic_regexp = r'^(\s*)<s*(VirtualHost)\s+[^>]*:80\s*>.*'
        result = re.search( basic_regexp, source, re.MULTILINE | re.IGNORECASE )    
        self.assertNotEqual( result, None )
        
        v.set_port( None )
        self.assertEqual( v.get_port(), None )
        source = p.get_source()
        basic_regexp = r'^(\s*)<s*(VirtualHost)\s+[^>]*\s*>.*'
        result = re.search( basic_regexp, source, re.MULTILINE | re.IGNORECASE )    
        self.assertNotEqual( result, None )    
        
if __name__ == "__main__":
    outt = ""
    unittest.main()  
      
    """p = ApacheParser()
    p.load('datafiles/vhost.conf')
    p.dump_xml()
    print p.open_child.key"""
