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

class FakeLine(object):
    value = None
    def set_raw_value(self, value): self.value = value
    def get_raw_value(self): return self.value

class LineTest ( unittest.TestCase ):
    def test_init(self):
        pass

class OptionsTest ( unittest.TestCase ):
    def test_len(self):
        line = FakeLine()
        o = Options( line )
        self.assertEqual( len(o), 0 )        
        self.assertFalse( bool(o ))
        line.value = 'example.net'
        self.assertEqual( len(o), 1 )
        self.assertTrue( bool(o ))
        line.value = 'example.net www.example.net'
        self.assertEqual( len(o), 2 )
        line.value = 'example.net www.example.net beta.example.net'
        self.assertEqual( len(o), 3 )
        line.value = None
        self.assertEqual( len(o), 0 )
        line.value = ''
        self.assertEqual( len(o), 0 )        
        
    def test_get_item(self):
        #building from scratch
        line = FakeLine()
        o = Options( line )
        o.append( 'example.net' )
        self.assertEqual( o[0], 'example.net' )        
        #existing value
        line = FakeLine()
        o = Options( line )
        line.value = 'example.net www.example.net beta.example.net'
        self.assertEqual( o[0], 'example.net' )
        self.assertEqual( o[1], 'www.example.net' )
        self.assertEqual( o[2], 'beta.example.net' )
        self.assertEqual( o[0:1], ['example.net'] )
        self.assertEqual( o[0:-1], ['example.net', 'www.example.net'] )
    def test_get_set_options (self):
        line = FakeLine()
        o = Options( line )
        self.assertEqual( list( o ), [])
        line.value = 'example.net www.example.net beta.example.net'
        self.assertEqual( list( o ), ['example.net', 'www.example.net', 'beta.example.net'])
        o.set( ['annodomini.com', 'www.annodomini.com'] )
        self.assertEqual( len(o), 2 )
        self.assertEqual( list( o ), ['annodomini.com', 'www.annodomini.com'] )
        o.set( [] )
        self.assertEqual( len(o), 0 )
        o.set( ['annodomini.com', 'www.annodomini.com'] )
        o.set( None )
        self.assertEqual( len(o), 0 )
        #let's test the set() method
        line = FakeLine()
        o = Options( line )
        o.set( ['example.net', 'www.example.net', 'beta.example.net'] )
        self.assertEqual( list( o ), ['example.net', 'www.example.net', 'beta.example.net'])
    def test_get_set_int_options(self):
        #options shuold always be strings, int are nowhere to be found
        line = FakeLine()
        line.value = 'ErrorDocument'
        o = Options( line )
        o[0] = 666
        self.assertEqual( o[0],  "666")
    def test_set_item(self):
        line = FakeLine()
        o = Options( line )
        line.value = 'example.net www.example.net'
        o[0] = 'annodomini.com'
        self.assertEqual( o[0], 'annodomini.com' )
        o[1] = 'www.annodomini.com'
        self.assertEqual( o[1], 'www.annodomini.com' )
        #empty values will cancel the index (and cause everything to scale)
        line.value = 'example.net www.example.net'
        o[0] = ''
        self.assertEqual( o[0], 'www.example.net' )
        line.value = 'example.net www.example.net'
        o[0] = None
        self.assertEqual( o[0], 'www.example.net' )
        try:
            o[1] = 'error.example.net'
            self.assertFalse( 'expecting IndexError exception' )
        except IndexError:
            pass
        
    def test_del_item (self):
        line = FakeLine()
        o = Options( line )
        line.value = 'example.net www.example.net beta.example.net'
        del o[0]
        self.assertEqual( list(o) , ['www.example.net', 'beta.example.net'] )
        del o[1]
        self.assertEqual( list(o) , ['www.example.net'])
        del o[0]
        self.assertEqual( list(o) , [])
        try:
            del o[0]
            self.assertFalse( 'expecting IndexError exception' )
        except IndexError:
            pass
    def test_append ( self ):
        line = FakeLine()
        o = Options( line )
        line.value = 'example.net www.example.net beta.example.net'
        o.append('xxx')
        self.assertEqual( list(o) , ['example.net','www.example.net', 'beta.example.net', 'xxx'] )
    def test_insert ( self ):
        line = FakeLine()
        o = Options( line )
        line.value = 'example.net www.example.net beta.example.net'
        o.insert(1, 'xxx')
        self.assertEqual( list(o) , ['example.net','xxx','www.example.net', 'beta.example.net'] )
    def test_remove ( self ):
        line = FakeLine()
        o = Options( line )
        line.value = 'example.net www.example.net beta.example.net'
        o.remove('www.example.net')
        self.assertEqual( list(o) , ['example.net', 'beta.example.net'] )
        
if __name__ == "__main__":
    outt = ""
    unittest.main()  
      
