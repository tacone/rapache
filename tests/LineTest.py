#    This file is copyrighted by Stefano Forenza <stefano@stefanoforenza.com>
#
#    The code below is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License or (if you prefer) the 
#    GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    The code below is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    To read the actual licenses see <http://www.gnu.org/licenses/>.
		
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
        #again, but using a tuple
        l = Line()
        l.opts = ('a','b')
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
        
        l.parse('AuthName "Enter your password"')
        self.assertEqual( l.value,  "Enter your password")
        
        l.parse('AuthName "Enter your \"password\""')
        self.assertEqual( l.value,  'Enter your "password"')
    def test_changed(self):
        c = etree.Element("line")
        c.set('directive','DocumentRoot')
        c.set('value', '/var/www')
        l = Line( c )
        self.assertTrue ( l.changed() )
        l = Line(c)
        l.parse('DocumentRoot /var/www')
        self.assertFalse ( l.changed() )
        l.value = '/srv/www'
        self.assertTrue ( l.changed() )
        l = Line(c)
        l.parse('DocumentRoot /var/www')
        self.assertFalse ( l.changed() )
        l.key = 'ServerAlias'
        self.assertTrue ( l.changed() )
        
    def test_get_set_value(self):        
        l = Line()
        l.key = 'DocumentRoot'
        l.value = '/var/www' 
        self.assertEqual( l.get_as_str(),  'DocumentRoot /var/www\n')
        self.assertEqual( l.value,  '/var/www' )        
        self.assertEqual( list(l.opts),  [ '/var/www' ])
        # let's test quoting
        l = Line()
        l.key = 'AuthName'
        l.value = 'Enter your password' 
        self.assertEqual( l.get_as_str(),  'AuthName "Enter your password"\n')
        self.assertEqual( l.value,  'Enter your password' )        
        self.assertEqual( list(l.opts),  [ 'Enter your password' ])
        #multiple options
        l = Line()
        l.key = 'ServerAlias'
        l.opts =  'example.org',  'example.net'
        self.assertEqual( l.get_as_str(),  'ServerAlias example.org example.net\n')
        self.assertEqual( l.value,  'example.org example.net' )        
        self.assertEqual( list(l.opts),  [ 'example.org',  'example.net' ] )
        
        #multiple with quoted string
        l = Line()
        l.key = 'ErrorDocument'
        l.opts =  '404',  'Not a good idea'
        self.assertEqual( l.get_as_str(),  'ErrorDocument 404 "Not a good idea"\n')
        self.assertEqual( l.value,  '404 "Not a good idea"' )        
        self.assertEqual( list(l.opts),  ['404',  'Not a good idea' ] )
if __name__ == "__main__":
    unittest.main()  
