import os


def command( command ):        
    print "COMMAND: "+command
    return os.system( command )
    """
    try:
        retcode = call("mycmd" + " myarg", shell=True)
        if retcode < 0:
            print >>sys.stderr, "Child was terminated by signal", -retcode
        else:
            print >>sys.stderr, "Child returned", retcode
    except OSError, e:
        print >>sys.stderr, "Execution failed:", e
    """