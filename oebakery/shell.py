import sys
import os
import subprocess

from oebakery import *


def call(cmd, dir=None, quiet=False, success_returncode=0):
    logger.debug("call: %s", cmd)

    if type(cmd) == type([]):
        cmdlist = cmd
        cmd = cmdlist[0]
        for arg in cmdlist[1:]:
            cmd = cmd + ' ' + arg

    if dir:
        if not os.path.exists(dir):
            return None
    else:
        dir = ""

    # Git seems to have a problem with long paths __and__ generates
    # long relative paths when run from a symlinked path.  To
    # workaround this, we always switch to realpath before running any
    # commands.
    rdir = os.path.realpath(dir)

    pwd = os.getcwd()
    chdir(rdir, quiet=True)

    if not quiet:
        if dir:
            print '%s> %s'%(dir, cmd)
        else:
            print '> %s'%(cmd)

    retval = None
    if quiet:
        process = subprocess.Popen(cmd, shell=True, stdin=sys.stdin,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        output = process.communicate()[0]
        if process.returncode == success_returncode:
            retval = output

    else:
        returncode = subprocess.call(cmd, shell=True, stdin=sys.stdin)
        if returncode == success_returncode:
            retval = True

    chdir(pwd, quiet=True)

    return retval
