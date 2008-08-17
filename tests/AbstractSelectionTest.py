import unittest
import sys
sys.path.append('../RapacheCore')
from LineElement import *
import re

class FakeLine:
    def __init__(self, v = None):
        self.value = v
class SimpleSelection(AbstractSelection):
    def __init__(self):
        #self._list = []
        self.__dict__['_list'] = []
    def _get_list( self ):    
        return self._list
    def _set_list(self, list):
        if list is None: list = []
        self._list = []
        
class AbstractSelectionTest( unittest.TestCase ):
    def test_init (self):
        s = SimpleSelection()
        s.append(FakeLine("a"))
        s.append(FakeLine("b"))
        s.append(FakeLine("c"))
        self.assertEquals( s.value, "c" )
        try:
            s.goodstuffforcheap
            self.assertTrue(False)
        except AttributeError:
            pass
        
        s = SimpleSelection()
        try:
            s.value
            self.assertTrue(False)
        except IndexError:
            pass
if __name__ == "__main__":
    unittest.main()  
