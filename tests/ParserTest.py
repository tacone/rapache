import unittest
import sys
sys.path.append('../RapacheCore')
from LineElement import *
import re

        
class ParserTest( unittest.TestCase ):
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
        p = Parser()
        p.load( self.apache2conf )
        self.assertTrue( p.linescount() > 0 )
    def test_getdirective(self):
        p = Parser()
        p.load( self.apache2conf )
        #right case
        self.assertEqual ( len( p.Include ), 6 )
        #lowercase
        self.assertEqual ( len( p.include ), 6 )
        #lowercase
        self.assertEqual ( len( p.include ), 6 )
        #nonexisting
        self.assertEqual ( len( p.mexico ), 0 )
    def test_get_value(self):
        expected = [
              '/etc/apache2/mods-enabled/*.load'
            , '/etc/apache2/mods-enabled/*.conf'
            , '/etc/apache2/httpd.conf'
            , '/etc/apache2/ports.conf'
            , '/etc/apache2/conf.d/'
            , '/etc/apache2/sites-enabled/']
        p = Parser()
        p.load( self.apache2conf )
        self.assertEqual( p.Include.value, '/etc/apache2/sites-enabled/' )
        for idx, directive in enumerate(p.Include): 
            self.assertEqual( directive.value, expected[idx])
        
        #p.dump_xml(True)    
        #testing subtag retrieval
        self.assertEqual( len( p.IfModule ), 2 )
        #last Options from last <Directory>, plus case insensitive
        self.assertEqual( p.ifmodule.threadsperchild.value, '25')
        #ThreadPerChild is not present in the first <IfModule>
        try:
            self.assertEqual( p.ifmodule[0].threadsperchild.value, '25')
            self.assertTrue(False)
        except IndexError:
            pass
        #it is in the last one
        self.assertEqual( p.ifmodule[-1].threadsperchild.value, '25')
if __name__ == "__main__":
    unittest.main()  
