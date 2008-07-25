# Rapache - Apache Configuration Tool
# Copyright (C) 2008 Stefano Forenza,  Jason Taylor, Emanuele Gentili
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
sys.path.append('../RapacheCore')
from Shell import *
import unittest


class ShellTest( unittest.TestCase ):
    def test_authorization (self):
        """Tests basic features. Auth reset, command return code and sudoing"""
        c = CommandHandler()
        print c.sudo_reset()
        self.assertTrue( c.is_auth_needed() )
        code, out, err = c.sudo_execute(["head", "/var/log/syslog"], "Pwd FTW !")
        if ( code != 0 ):
            self.assertTrue( c.is_auth_needed() )
            print """You have provided a wrong password. Please repeat
            the test again and provide a working password """
            exit()
        self.assertFalse( c.is_auth_needed() )
        c.sudo_reset()
        self.assertTrue( c.is_auth_needed() )
        code, out, err = c.execute(["ls"])
        self.assertEqual( code, 0 )
        
        
        
        #code, out, err = c.sudo_execute(["head", "/var/log/syslog"], "Pwd FTW !")
        

if __name__ == "__main__":
    unittest.main()
    