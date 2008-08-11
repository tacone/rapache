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
import tempfile
import getpass
import subprocess
import sys
from subprocess import *
import traceback
import time
import glob
import operator
import Configuration

class CommandLogEntry:

    def __init__(self, command):
        self.command = subprocess.list2cmdline(command)
        self.returncode = None
        self.output = None
        self.error = None


class CommandHandler:

    def __init__(self, ssh_server="localhost", ssh_port=None, ssh_username=None, ssh_password=None):
       
        # Verboseness
        # 0 = No output
        # 1 = prints the command and its return code
        # 2 = Command output
        self.auto_backup = False
        self.verbose = 0
        self.command_log = []
        # let's make the object stateful, no duplicate password
        # typing needed for our users
        self.__password = None
        
        # SSH connection details     
        self.ssh_server = ssh_server
        self.ssh_port = ssh_port
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password

    def __get_backup_path(self, path):
        # ~/.rapache/backup/server/file_path/datestamp.bak
        backup_path = os.path.expanduser(os.path.join("~/.rapache/backup", self.ssh_server, path[1:]))
        if not os.path.exists( os.path.dirname(backup_path) ):
            os.makedirs(os.path.dirname(backup_path))
        return backup_path
    
    # returns an array of [[path, file creation time]]
    def get_backup_files(self, path):
        backup_path = self.__get_backup_path(path)
        flist = glob.glob(backup_path + " *.bak")
        for i in range(len(flist)):
            statinfo = os.stat(flist[i])
            flist[i] = flist[i], statinfo.st_ctime
        flist.sort(key=operator.itemgetter(1))
        flist.reverse()
        return flist

    def read_file_version(self, path, date_stamp):
        backup_path = self.__get_backup_path(path)
        path = backup_path + " " + date_stamp + ".bak"
        if self.verbose >= 1:
            print "READ BACKUP VERSION : " + path
        f = open(path, "r")
        content = f.read()
        f.close()
        return content

    def create_backup(self, path, new_content):
        existing_content = self.read_file(path)
        backup_path = self.__get_backup_path(path)
        backup_file = backup_path + " " +time.strftime("%y-%m-%d %H:%M:%S.bak", time.localtime() )

        if existing_content:

            if new_content != existing_content:
                # back up, the file has changed

                if self.verbose >= 1:
                    print "CREATE BACKUP : " + backup_file
                
                f = open(backup_file, "w")
                f.write(existing_content)
                f.close()

                # cleanup backups keep last N - TODO - make a config option
                flist = self.get_backup_files(path)
                # delete older entries                    
                for i in range(Configuration.NUMBER_OF_BACKUPS, len(flist)):
                    if self.verbose >= 1:
                        print "REMOVE BACKUP : " + flist[i][0]
                    os.remove( flist[i][0] )
                
                return True # file existed and changed backup made
                
            return False # no change in file content
        
        if new_content:
            return True # file dosnt exist but there is new content
            
        return False # file dosnt exist and no new content
       
    def read_file(self, path):
        if self.verbose >= 1:
            print "READING : " + path
        # TODO: add ssh handler
        if os.path.exists(path):
            f = open(path, "r")
            result = f.read()
            f.close()
            return result
        return ""
    
    def write_file(self, path, content):

        if self.create_backup(path, content):
            
            if self.verbose >= 1:
                print "WRITING : " + path
            
            # Update local backup copy
            local_path = self.__get_backup_path(path)
            f = open(local_path, "w")
            f.write(content)
            f.close()

            # copy file now using sudo
            self.sudo_execute( ["cp", local_path, path] )

    def listdir(self, path):
        return os.listdir( path )

    def create_complete_path ( self, complete_path ):
        if self.verbose >= 1:
            print "Creating Path: " + complete_path
        tokens = complete_path.split( '/' )
        del tokens[ 0 ]        
        path = '/'
        for piece in tokens:
            path = os.path.join(path, piece)
            print path
            if not self.exists( path ):
                try:
                    self.sudo_execute( ["mkdir", path] )
                except:
                    print "error on creating path"+path
                    return False                   
        return True 


    def exists(self, path):
        return os.path.exists(path)
        
    def readlink(self, path):
        return os.readlink(path)
           
    def move(self, source, destination):
        self.sudo_execute( ["mv", source, destination] )
   
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
        #command = [ 'head', '/var/log/syslog', '-n 1' ]
        command = [ 'sudo', '-v' ]
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
#command.verbose = 1

if __name__ == "__main__":
    c = CommandHandler()
    c.verbose = 2
    #print c.is_auth_needed()
    
    print c.sudo_reset()       
    code, out, err = c.sudo_execute(["head", "/var/log/syslog"], "Pwd FTW !")
    code, out, err = c.sudo_execute(["head", "/var/log/syslog"], "Pwd FTW !")
   
