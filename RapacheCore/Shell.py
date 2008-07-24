import os

# <--- shit
#def command( command ):        
#    print "COMMAND: "+command
#    return os.system( command )
#    """
#    try:
#        retcode = call("mycmd" + " myarg", shell=True)
#        if retcode < 0:
#            print >>sys.stderr, "Child was terminated by signal", -retcode
#        else:
#            print >>sys.stderr, "Child returned", retcode
#    except OSError, e:
#        print >>sys.stderr, "Execution failed:", e
#    """ 
    
import sys   
import gksu2
import getpass
import subprocess
import StringIO
import sys
from subprocess import *
import traceback

class CommandLogEntry:

    def __init__(self, command):
        self.command = subprocess.list2cmdline(command)
        self.returncode = None
        self.output = None
        self.error = None


class CommandHandler:

    def __init__(self):
        # Verboseness
        # 0 = No output
        # 1 = prints the command and its return code
        # 2 = Command output
        self.verbose = 0
        self.command_log = []
        # let's make the object stateful, no duplicate password
        # typing needed for our users
        self.__password = None
        
    def __get_password(self, description, prompt="Password: "):
        
        ctx = gksu2.Context()
        ctx.set_message(description)
        ctx.set_command(subprocess.list2cmdline(["ls","/root"]))
        ctx.set_grab(True)        
        
        return gksu2.ask_password_full(ctx, prompt) # how does su_full invoke keychain options?
    
    def __sudo_popen (self, command, password ): 
        #don't enable the following line
        #print "using password:", password
        
        # prepend sudo to command and allow piping in 
        command.insert(0, "sudo")
        command.insert(1, "-S")
        p = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        #we need a try catch to avoid tracebacks to be printed
        #as they would show the password
        try:    
            p.stdin.write( password )
        except:
            #don't enable the following line as you password
            #will be printed out
            #traceback.print_exc() #<-- CAUTION !
            
            print "ERROR: in __sudo_popen()"
            pass
        return p
    
    def is_auth_needed (self):        
        if not self.__password: return True
        
        #only ASCII chars in the fake pass, or it won't work
        #because we have not encoding declared in this file
        #http://www.python.org/dev/peps/pep-0263/
        fakepass= 'xxxASAISUHAISGHauyguyagUDBhb2156412-,1-2.,1212'
        command = [ 'head', '/var/log/syslog', '-n 1' ]
        p = self.__sudo_popen( command, fakepass)
        output, error = p.communicate()
        returncode = p.returncode        
        self.__output(command, returncode, output, error)    
        print "needs login:", returncode
        if returncode == 0:
            return False
        else:          
            self.__password = None      
            return True
                
    # Description will be discarded
    def execute(self, command, description = None ):
        returncode = 0
        output = None
        error = None
        # excute the command, capture output, error and return code
        p = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE) 
        output, error = p.communicate()
        returncode = p.returncode
        self.__output(command, returncode, output, error)
        return (returncode, output, error)
   
    def __output (self, command, returncode, output, error ):
        string_command = subprocess.list2cmdline(command)
        if self.verbose > 0:
            print "COMMAND (return code: "+str(returncode)+"): "+ string_command
        if self.verbose > 1:
            print output
        if error:
            sys.stderr.write( error+"\n")
        
    def sudo_reset (self):
        self.__password = None
        command = ['sudo', '-K' ]
        p = Popen( command, stdout=PIPE, stderr=PIPE, stdin=PIPE) 
        output, error = p.communicate()
        returncode = p.returncode
        self.__output(command, returncode, output, error)
        
    def sudo_execute(self, command, description = "Super user priviledges are required to perform this operation"):
        #log = CommandLogEntry(command)
        #self.command_log.append( log )
       
        returncode = 0
        output = None
        error = None
        new_password = None
        
        auth_needed = self.is_auth_needed()
        
        if auth_needed :            
            #let's ask the user for a new password
            if not self.__password :
                try:
                    new_password = self.__get_password(description)
                except:
                    returncode = 1
                    error = "Incorrect password"
            
        if (not auth_needed) or new_password:
            #if already authorized let's fake a random password
            if new_password:
                password = new_password
            elif self.__password:
                password = self.__password
            else:
                #let's just fake it. It will work anyways
                password = 'xxx'            
            
            # excute the command, capture output, error and return code
            p = self.__sudo_popen( command, password )      
            #p.stdin.write(password) 
            output, error = p.communicate()
            returncode = p.returncode
            self.__output(command, returncode, output, error)
            
        if new_password: 
            self.__password = 'asasasaasas'
            #self.__password = new_password

        #log.returncode = returncode
        #log.output = output
        #log.error = error
        
        return (returncode, output, error)

# Look ma'! A singleton !
command = CommandHandler()    
    
if __name__ == "__main__":
    c = CommandHandler()
    c.verbose = 2
    #print c.is_auth_needed()
    
    print c.sudo_reset()       
    code, out, err = c.sudo_execute(["head", "/var/log/syslog"], "Pwd FTW !")
    code, out, err = c.sudo_execute(["head", "/var/log/syslog"], "Pwd FTW !")
   