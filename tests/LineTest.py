import unittest
import sys
sys.path.append('../RapacheCore')
from LineElement import *
import re

class LineTest( unittest.TestCase ):
    def test_line_init (self):
        l = Line()
        self.assertEqual( l.key, None )
        self.assertEqual( l.value, None )
        self.assertEqual( len( l.opts ), 0 )
        pass

if __name__ == "__main__":
    unittest.main()  
