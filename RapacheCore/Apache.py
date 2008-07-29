import sys
import os
import urllib
import urllib2

sys.path.insert(1, os.path.join(sys.path[0], os.path.pardir))
from RapacheCore import Shell

class Apache():

    def __init__(self):
        self.server = "localhost"

    def get_status(self):
        # 0 not running, 1 service started, 2 can get an http connection
        if not self.is_running():
            return 0
        if not self.is_reachable():
            return 1
        return 2   

    # is service running
    def is_running(self):
        # Check if python2 is running
        returncode, output, error = Shell.command.execute(["pidof", "apache2"])
        return len(output.strip()) > 0
 
    # is http reachable
    def is_reachable(self):
        try:
            p = urllib2.urlopen( "http://" + self.server )
            info = p.geturl()
            p.close()
            return True
        except urllib2.HTTPError, e:
            # if we got an error code from the server then its running
            return True
        except urllib2.URLError, e:
            # http error asume we could not connect
            return False

    def start(self):
        Shell.command.sudo_execute(["apache2ctl", "start"])
        return
        
    def stop(self):
        Shell.command.sudo_execute(["apache2ctl", "stop"])
        return
    
    def restart(self):
        Shell.command.sudo_execute(["apache2ctl", "restart"])
        return
 
a = Apache()
print a.is_running() 
print a.is_reachable()    
