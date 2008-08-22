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
        self.__dict__['_list'] = []
    def _get_list( self ):    
        return self._list
    def _set_list(self, list):
        if list is None: list = []
        self._list = list
        
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
    def test_list_wrapped (self):
        s = SimpleSelection()
        first = FakeLine("a")
        s.append(first)
        second = FakeLine("b")
        s.append(second)
        third = FakeLine("c")
        s.append(third)
        self.assertEquals( third,  s[2])
    def test_set_value(self):
        s = SimpleSelection()
        s.append(FakeLine("a"))
        s.append(FakeLine("b"))
        s.append(FakeLine("c"))
        s.value = 'z'
        self.assertEquals( s.value,  'z' )
if __name__ == "__main__":
    unittest.main()  
