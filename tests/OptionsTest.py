import unittest
import sys
sys.path.append('../RapacheCore')
from LineElement import *
import re

class FakeLine(object):
    value = None

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
        self.assertEquals( list( o ), [])
        line.value = 'example.net www.example.net beta.example.net'
        self.assertEquals( list( o ), ['example.net', 'www.example.net', 'beta.example.net'])
        o.set( ['annodomini.com', 'www.annodomini.com'] )
        self.assertEqual( len(o), 2 )
        self.assertEquals( list( o ), ['annodomini.com', 'www.annodomini.com'] )
        o.set( [] )
        self.assertEqual( len(o), 0 )
        o.set( ['annodomini.com', 'www.annodomini.com'] )
        o.set( None )
        self.assertEqual( len(o), 0 )
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
      
