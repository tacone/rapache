import unittest
import sys
sys.path.append('../RapacheCore')
from LineElement import *
import re

class LineTest( unittest.TestCase ):
    def test_init (self):
        l = Line()
        self.assertEqual( l.key, None )
        self.assertEqual( l.value, None )
        self.assertEqual( len( l.opts ), 0 )
        self.assertTrue( isinstance(l.opts, Options))
        pass
    def test_element__init (self):
        c = etree.Element("line")
        c.set('directive','DocumentRoot')
        c.set('value', '/var/www')
        l = Line( c )
        self.assertEqual( l.element.attrib['directive'], 'DocumentRoot' )
        self.assertEqual( l.element.attrib['value'], '/var/www' )
        self.assertEqual( l.key, 'DocumentRoot' )
        self.assertEqual( l.value, '/var/www' )
        
    def test_value_get_set(self):
        l = Line()
        self.assertEqual( l.value, None )
        l.value = "/var/www"
        self.assertEqual( l.value, "/var/www" )                
    def test_opts_set(self):
        #testing .opts attrib. can't be overriden
        l = Line()
        l.opts = ['a','b']
        #l.opts should still be an Options instance, not a list
        self.assertTrue( isinstance(l.opts, Options))
        self.assertEqual( list(l.opts), ['a','b'])
    def test_parse(self):
        l = Line()
        expected_values =[
            [ 'DocumentRoot /var/www/', '/var/www/' ],
            #should strip trailing spaces
            [ 'DocumentRoot /var/www/    ', '/var/www/' ],
            #should strip preceding spaces
            [ 'DocumentRoot   /var/www/    ', '/var/www/' ], 
            #should return all the options as one single string
            [ 'ServerAlias www.example.com beta.example.com ', 'www.example.com beta.example.com' ],
            #should return None
            [ 'ServerAlias', None]
          ]
        for case in expected_values:
            string, expected = case  
            l.parse(string)        
            self.assertEqual(l.value, expected)
        
        expected_keys =[
         [ 'DocumentRoot /var/www/', 'DocumentRoot' ],
         [ '\t\t  DocumentRoot /var/www/', 'DocumentRoot' ]
        ]
        for case in expected_keys:
            string, expected = case  
            l.parse(string)        
            self.assertEqual(l.key, expected)
        l.parse(string) 
        
        l.parse('ServerAlias www.example.com beta.example.com ')
        self.assertEqual(list(l.opts),['www.example.com','beta.example.com'])
if __name__ == "__main__":
    unittest.main()  
