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
