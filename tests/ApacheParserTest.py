import unittest
import sys
sys.path.append('../RapacheCore')
from ApacheParser import *

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
# let the file end with this line, don't add empty \n or tests will fail"""
    
class ApacheParserTest ( unittest.TestCase ):
    apache2conf = 'datafiles/apache2.conf'
    apache2conf_expected  = {
     'Group': '${APACHE_RUN_GROUP}',
     'StartServers': '2',
     'ThreadsPerChild': '25',
     'HostnameLookups': 'Off',
     'LockFile': '/var/lock/apache2/accept.lock',
     'KeepAlive': 'On',
     'Include': '/etc/apache2/sites-enabled/',
     'ServerRoot': '/etc/apache2',
     'MinSpareServers': '5',
     'MinSpareThreads': '25',
     'MaxClients': '150',
     'User': '${APACHE_RUN_USER}',
     'MaxRequestsPerChild': '0',
     'Deny': 'from all',
     'ServerSignature': 'On',
     'Timeout': '300',
     'KeepAliveTimeout': '15',
     'AccessFileName': '.htaccess',
     'Order': 'allow,deny',
     'MaxSpareServers': '10',
     'ServerTokens': 'Full',
     'ErrorLog': '/var/log/apache2/error.log',
     'LogLevel': 'warn',
     'LogFormat': '#ERROR',
     'MaxSpareThreads': '75',
     'MaxKeepAliveRequests': '100',
     'DefaultType': 'text/plain',
     'PidFile': '${APACHE_PID_FILE}'
    }
    optionsconf = 'datafiles/options.conf'
    vhostconf = 'datafiles/vhost.conf'
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
    
    def old_load(self):
        p = ApacheParser()
        p.load( self.apache2conf )
        self.assertTrue( p.linescount() > 0 )
        #p.dump_xml()
    def old_get_value(self):
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
    def old_set_value (self):
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
    def old_has_option(self):
        p = Parser()
        p.load( self.optionsconf )
        self.assertTrue( p.has_option( 'ServerAlias', 'www.bart.loc' ) )
        self.assertTrue( p.has_option( 'ServerAlias', 'test.bart.loc' ) )
        self.assertFalse( p.has_option( 'ServerAlias', 'notex.bart.loc' ) )
        self.assertFalse( p.has_option( 'ServerAlias', '' ) )
        self.assertFalse( p.has_option( 'ServerAlias', None ) )
        self.assertFalse( p.has_option( 'ServerAlias', True ) )
    def old_get_options(self):
        p = Parser()
        p.load( self.optionsconf )
        expected = ['www.bart.loc', 'test.bart.loc']
        options = p.get_options( 'ServerAlias' )
        self.assertEqual( options, expected )
        self.assertEqual( p.get_options( 'NoOptions' ), [] )
    def old_get_directive (self):
        p = Parser()
        p.load( self.apache2conf )
        for key in self.apache2conf_expected :
            expected = self.apache2conf_expected[ key ]
            if expected == '#ERROR':
                print "Please cover parsing of ",key," in apache2.conf with tests"
            else:
                self.assertNotEquals ( p.get_directive(key).find(key), -1 )
                self.assertNotEquals ( p.get_directive(key).find(expected), -1 )
        
    def old_set_directive (self):
        p = Parser()
        p.load( self.apache2conf )
        length = p.linescount()
        
        p.set_directive( "KeepAliveTimeout", "\t\tKeepAliveTimeout 30" )
        self.assertEqual( length, p.linescount() )
        self.assertEqual( p.get_value( 'KeepAliveTimeout' ), "30" )
        
        p.set_directive( "NewDirective", "\t\tNewDirective MyValue" )
        self.assertEqual( p.get_value( 'NewDirective' ), 'MyValue' )
        self.assertEqual( length +1 , p.linescount() )
        
    def old_add_option(self):
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
        
    def old_remove_option(self):
        p = Parser()
        p.load( self.optionsconf )
        expected = ['www.bart.loc', 'test.bart.loc', 'new.bart.loc' ]
        p.remove_option( 'ServerAlias', 'new.bart.loc' )
        
        options = p.get_options( 'ServerAlias' )
        
    def old_get_content(self):
        p = Parser()
        p.load( self.optionsconf )
        content = p.get_content()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13 )
        #do lines contain extra  trailing \n ?
        self.assertEqual( len( "/n".join( content ).split( "\n" )), 13 )
    def old_set_content_from_string (self):
        p = Parser()
        p.set_content_from_string( STRING_VHOST )
        content = p.get_content()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13 )
        #do lines contain extra  trailing \n ?
        self.assertEqual( len( "\n".join( content ).split( "\n" )), 13 )
    def old_is_tag_open(self):
        p = Parser()
        for line in self.valid_tags:
            result = p.is_tag_open( line )
            expected = self.valid_tags[line]
            self.assertEquals( result, expected )
        for line in self.invalid_tags:
            result = p.is_tag_open( line )
            self.assertFalse( result )
    def test_nesting (self):   
        print '=========xxxxxxxxxxxxxxxxxxxxx'
        p = Parser()
        p.load( self.vhostconf )
        #p.dump_xml( True )
        self.assertEqual( p.linescount(), 3)
if __name__ == "__main__":
    unittest.main()    
    """p = ApacheParser()
    p.load('datafiles/vhost.conf')
    p.dump_xml()
    print p.open_child.key"""