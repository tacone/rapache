

import paramiko
import subprocess

if __name__ == '__main__':

    t = paramiko.Transport(("localhost", 22))
    t.connect(username="jason", password="goodwill")
    chan = t.open_session()
    
    chan.exec_command(subprocess.list2cmdline(["ls", "~/"]))
    return_code = chan.recv_exit_status()

    stdout = ""
    next = chan.recv(100)
    while len(next) > 0:
        stdout = stdout + next
        next = chan.recv(100)
        
    stderr = ""
    next = chan.recv_stderr( 100)    
    while len(next) > 0:
        stderr = stderr + next
        next = chan.recv_stderr(100)  
    
    chan.close()
    t.close()

    print return_code
    print stdout
    print stderr
    


