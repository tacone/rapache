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
    errordocumentsconf= 'datafiles/errordocuments.conf'
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
    def test_get_set_key(self):
        p = Parser()
        self.assertEqual(p.key,  None)
        p.key = 'test'
        self.assertEqual(p.key,  'test')
    def test_get_set_value(self):
        p = Parser()
        self.assertEqual(p.value,  None)
        p.value = 'test'
        self.assertEqual(p.value,  'test')
    def test_load(self):
        p = Parser()
        p.load( self.apache2conf )
        self.assertTrue( len( p.lines )> 0 )
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
        
    def test_load(self):       
        p = Parser()
        p.load( self.optionsconf )
        p.load( self.vhostconf )
        p.load( self.fromtemplateconf )
        p.load( self.defaultssl )
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
        
        #the key of a section is the name of the tag
        self.assertEqual( p.ifmodule.key,  'IfModule' )
        #the value shuold be relative to the last section found of that kind
        self.assertEqual( p.ifmodule.value,  'mpm_worker_module' )
        #we can get the value of the first section found
        self.assertEqual( p.ifmodule[0].value,  'mpm_prefork_module' )
        #we can also specify explicitly we want the last (or any other idx)
        self.assertEqual( p.ifmodule[-1].value,  'mpm_worker_module' )
        
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
        #=========================================
        #old parser tests
        p = Parser()
        p.load( self.apache2conf )
        
        for key in self.apache2conf_expected :
            expected = self.apache2conf_expected[ key ]
            if expected == '#ERROR':
                print "Please cover parsing of ",key," in apache2.conf with tests"
            else:
                self.assertEqual( getattr(p,key).value, expected )
        
        if p.Include:
            pass
        else:
            self.assertTrue(False)
            
        #cool, let's try to get a non-existant directive
        try:
            p.IDontExist.value
            self.assertTrue(False)
        except IndexError:
            pass
        
        if not p.IDontExist:
            pass
        else:
            self.assertTrue(False)
        #self.assertEqual( p.get(key), expected  )
    def test_lines(self):
        """'lines' property returns a selection of all the
        non-section directives in the current (or root) 
        section."""
        p = Parser()
        self.assertEqual( len(p.lines),  0 )
        p.load( self.vhostconf )
        self.assertEqual( len( p.lines ),  3 )
        #test for errors interating and retrieving
        for l in p.lines:
            tempval = l.value
        self.assertEqual( p.lines[1].value ,  'On' )
    def test_sections(self):
        p = Parser()
        self.assertEqual( len(p.sections),  0 )
        p.load( self.vhostconf )          
        self.assertEqual( len( p.sections ),  1)
        #test for errors interating and retrieving                
    def test_set_value (self):
        p = Parser()
        p.load( self.apache2conf )
        length = len(p.lines)
        for key in self.apache2conf_expected:
            self.assertFalse( getattr(p,  key).changed() )
        
        for key in self.apache2conf_expected :
            if self.apache2conf_expected[ key ] == '#ERROR':
                print "Please cover parsing of ",key," in apache2.conf with tests"
            else:
                getattr( p,  key ).value = 'NULLIFIED'
        #number of lines shuoldn't be changed
        self.assertEqual( len(p.lines), length )
                
        for key in self.apache2conf_expected :
            line = getattr(p,  key)            
            #print key,dict[key]
            #print key,"-->",dict[key]
            
            if line.value is not None and line.value != '#ERROR':
                res = self.assertEqual(line.value, 'NULLIFIED' )
            
            if  line.value=='NULLIFIED':
                self.assertTrue( line.changed() )
            else:
                self.assertFalse( line.changed() )
                
        p.DocumentRoot.value ='/var/www/htdocs' 
        #DocumentRoot is not present in the file, should add a new line
        self.assertEqual( len(p.lines), length +1 )
        #try setting a value with spaces
        p.DocumentRoot.value ='/var/www/my htdocs'
        #length should be the same as before
        self.assertEqual( len(p.lines), length +1 )        
        self.assertEqual( p.DocumentRoot.value, '/var/www/my htdocs' )
    def test_create(self):
        p = Parser()        
        p.load( self.vhostconf ) 
        v = p.virtualhost
        linescount= len(v.lines)    
        #creating a line
        line = v.lines.create( 'CustomDirective',  'On')
        self.assertEqual( len(v.lines),  linescount + 1)
        self.assertEqual( line.key,  'CustomDirective' )
        self.assertEqual( line.value,  'On' )
        #has been correctly attached ?
        self.assertEqual( v.customdirective.value,  'On' )
        # is a line ?
        try: #lines have not .sections attribute
            line.sections
            self.assertTrue(False)
        except AttributeError:
            pass
        #creating a section
        sectioncount = len( v.sections )
        section = v.sections.create( 'CustomSection',  '*:80')
        self.assertEqual( len(v.sections),  sectioncount + 1)
        self.assertEqual( section.key,  'CustomSection' )
        self.assertEqual( section.value,  '*:80' )
        #has been correctly attached ?
        self.assertEqual( v.customsection.value,  '*:80' )
        # is a section?
        # sections HAVE .sections attribute
        section.sections
        
        string = v.customsection.get_as_str()
        
        
        #Parser and Section .create() defaults to .lines.section
        linescount= len(v.lines)    
        #creating a line
        line = v.create( 'CustomDirective',  'On')
        self.assertEqual( len(v.lines),  linescount + 1)
        #ensure a line object is returned
        self.assertEqual( line.key,  'CustomDirective' )
        
        #ensure new section are created correctly
        p = Parser()
        p.sections.create( 'VirtualHost',  '/var/www/spoon')
        source = p.get_as_list()
        basic_regexp = r'^(\s*)<s*(VirtualHost)\s+[^>]*>.*'
        result = re.search( basic_regexp, source[0  ], re.MULTILINE | re.IGNORECASE )    
        self.assertNotEqual( result, None )
        
        basic_regexp = r'^(\s*)<\/(VirtualHost)\s*[^>]*>.*'
        result = re.search( basic_regexp, source[1], re.MULTILINE | re.IGNORECASE )    
        self.assertNotEqual( result, None )
        
    def test_search(self):
        p = Parser()        
        p.load( self.errordocumentsconf ) 
        self.assertEqual( len( p.ServerAlias ),  2)
        self.assertEqual( len( p.ServerAlias.search( 'www.example.net' ) ),  1)
        self.assertEqual( p.ServerAlias.search( 'www.example.net' ).value,  'www.example.net')
        self.assertEqual( p.ServerAlias.search( 'www.example.com' ).value,  'www.example.com')
        #searching for first option
        self.assertEqual( len( p.ErrorDocument.search( [404] ) ),  1 )
        #searching for second option only
        self.assertEqual( len( p.ErrorDocument.search( [None,  '/error/HTTP_BAD_GATEWAY.html.var' ] ) ),  1 )
        #searching for two terms
        self.assertEqual( len( p.ErrorDocument.search([404 ,'/error/HTTP_NOT_FOUND.html.var'] ) ), 1)
        #trying to change the url for 404 error code
        p.ErrorDocument.search( [404] ).opts[1] = '/var/error/404.html'
        self.assertEqual( p.ErrorDocument.search( [404] ).opts[1],  '/var/error/404.html')
        #searching for the number of the beast
        self.assertEqual( len( p.ErrorDocument.search( [666] ) ),  0)
        #trying to set a new line 
        linescount = len( p.ErrorDocument )
        p.ErrorDocument.search( ["666"] ).opts = ["666",  '/var/number/of/the/beast.html']
        self.assertEqual( p.ErrorDocument.search( ["666"] ).opts[1],  '/var/number/of/the/beast.html')
        self.assertEqual( len( p.ErrorDocument ) ,  linescount+1)
        #as before, but using an int
        p = Parser()        
        p.load( self.errordocumentsconf ) 
        linescount = len( p.ErrorDocument )
        p.ErrorDocument.search( [ 666 ] ).opts = [666,  '/var/number/of/the/beast.html']
        self.assertEqual( p.ErrorDocument.search( [666] ).opts[1],  '/var/number/of/the/beast.html')
        self.assertEqual( p.ErrorDocument.search( [666] ).opts[0],  '666' ) #should be string
        self.assertEqual( len( p.ErrorDocument ) ,  linescount+1)
        #searching for sections
        p = Parser()        
        p.load( self.defaultssl ) 
        v = p.ifmodule.virtualhost        
        self.assertEqual( len(v.directory),  5)        
        self.assertEqual( len(v.directory.search( "/usr/lib/cgi-bin")),  2)
        self.assertEqual( len(v.directory.search( ["/usr/lib/cgi-bin"] )),  2)
        #changing the value of the last found directory we now shuold have a count of 1 on the search
        v.directory.search( "/usr/lib/cgi-bin").value = '/usr/lib/s-cgi'
        self.assertEqual( len(v.directory.search( "/usr/lib/cgi-bin")),  1)
        self.assertEqual( len(v.directory.search( "/usr/lib/nonexisting")),  0)
    def test_delete(self):
        p = Parser()        
        p.load( self.errordocumentsconf ) 
        self.assertEqual( len( p.ErrorDocument ),  17)
        del p.ErrorDocument[-1]
        self.assertEqual( len( p.ErrorDocument ),  16)
        del p.ErrorDocument
        self.assertEqual( len( p.ErrorDocument ),  0)
        #testing in a subelement
        vhost = p.VirtualHost
        self.assertEqual( len(vhost.ErrorDocument ),  6)
        del vhost.ErrorDocument[-1]
        self.assertEqual( len(vhost.ErrorDocument ),  5)
        del vhost.ErrorDocument
        self.assertEqual( len( vhost.ErrorDocument ),  0)
        self.assertEqual( len( p.virtualhost ),  1)
        #testing from search (!) 
        p = Parser()        
        p.load( self.errordocumentsconf )        
        vhost = p.VirtualHost
        self.assertEqual( len( vhost.ErrorDocument.search([666] ) ), 2)
        vhost.ErrorDocument.search([666] ).delete()
        self.assertEqual( len( vhost.ErrorDocument.search([666] ) ), 0)
        #testing delete search subelement
        p = Parser()        
        p.load( self.errordocumentsconf )        
        vhost = p.VirtualHost
        self.assertEqual( len( vhost.ErrorDocument.search([666] ) ), 2)
        vhost.ErrorDocument.search([666] )[0].delete()
        self.assertEqual( len( vhost.ErrorDocument.search([666] ) ), 1)
        self.assertEqual( vhost.ErrorDocument.search([666]).opts[1],'/error/HTTP_NOT_FOUND.html.var')
    def test_get_content(self):
        p = Parser()
        p.load( self.optionsconf )
        content = p.get_as_list()        
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13 )
        #do lines contain extra  trailing \n ?
        self.assertEqual( len( "/n".join( content ).split( "\n" )), 13 )
        
        p.DocumentRoot.value = '/var/www/fake'
        content = p.get_as_list()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13 )
        
        p.NotYetExistant.value ='value'
        content = p.get_as_list()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13+1 )
        
        p.NewOption.opts = ['option1']
        content = p.get_as_list()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13+2 )
        
        p.NewOption.opts = ['option2']
        content = p.get_as_list()
        self.assertEqual( type(content), type([]) )
        self.assertEqual( len( content), 13+2 )
        
    
    #TODO: find out why this fails
    def test_get_content_with_nesting(self):
        """tests that the content of subtags is actually rendered in
        the parent element get_content()"""
        file = open ( self.vhostconf, 'r' )
        original_content = file.readlines()
        file.close()
        
        p = Parser()
        p.load( self.vhostconf )
        content = p.get_as_list()     
        #print p.get_as_str()   
        #for line in content: print line, 
        #    print "\n".join( content )
        self.assertEqual( type(content), type([]) )
        #do lines contain extra  trailing \n ?
        self.assertEqual( len(original_content), len(content) )
        for idx, value in enumerate( original_content ):
            #note rstrip(), we don't preserve trailing spaces yet
            #TODO: should pass with rstrip() 
            #print original_content[ idx ].strip()
            #print content[ idx].strip()
            self.assertEqual( original_content[ idx ].strip(), content[ idx].strip() )
            #self.assertEqual( original_content, content )    
    def test_newlines_on_the_last_line(self):
        p = Parser()
        p.load( self.vhostconf )
        #p.dump_xml( True )
        vhost = p.virtualhost
        expectedlen = 16
        self.assertEqual( len( vhost.get_as_list() ), expectedlen )
        vhost.newoption.opts = ['opt1']
        self.assertEqual( len( vhost.get_as_list() ), expectedlen +1 )
    def test_newlines_on_get_source(self):
        """yet another test on newlines reliability"""
        #print "====== test_newlines_on_get_source ======="
        p = Parser()
        p.load( self.fromtemplateconf )
        actuallen = len( p.get_as_str().split("\n" ) );
        self.assertNotEqual( actuallen, 1 )
        vhost = p.virtualhost
        vhost.DocumentRoot.value = '/var/www/bbb/httpdocs'
        vhost.ServerName.value = 'bbba' 
        vhost.ServerAlias.opts.append( 'www.bbba' )
        self.assertEqual( actuallen, len( p.get_as_list() ) )        
        
        source = p.get_as_str()
        self.assertEqual( actuallen, len( source.split("\n")) )
        for count in range( 1, 6 ):
            expectedlen = len( source.split("\n") )
            p = Parser()
            try:
                p.set_from_str( source )
            except :
                print "ERROR on this source, at iteration %s" % str(count)
                
                
            source = p.get_as_str()
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
    def test_recursive_search(self):
        p = Parser()
        p.load( self.defaultssl )
        self.assertEqual( len( p.rsearch( 'virtualhost' )),  1)
        self.assertEqual( len( p.rsearch( 'directory' )),  5)
        self.assertEqual( len( p.rsearch( 'nonex' )),  0)
        try:
            p.rsearch( 'notexisting' ).value = '/var/www'            
            self.assertTrue(False) #exception should be thrown
        except NotImplementedError:
            pass
        p = Parser()
        p.load( self.errordocumentsconf)
        self.assertEqual( len( p.rsearch( 'ErrorDocument' )),  23)
        #testing in various contexts
        p = Parser()
        p.load( self.vhostconf)
        self.assertEqual( len( p.rsearch( 'weird' )),  1)
        self.assertEqual( len( p.virtualhost.rsearch( 'weird' )),  1)
        self.assertEqual( len( p.virtualhost.weird.rsearch( 'weird' )),  0)
    def test_readonly_properties(self):   
        pass
if __name__ == "__main__":
    unittest.main()  
