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
    