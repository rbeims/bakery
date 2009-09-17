__version__ = "0.0.0"

__all__ = [

    "get_topdir",
    "read_config",
    "call",

]

import sys, os, subprocess
from ConfigParser import SafeConfigParser


def get_current_topdir(dir):

    if dir == "/":
        return None

    if (os.path.exists("%s/conf/oe.conf"%dir) and
        os.path.exists("%s/openembedded/.git"%dir)):
        return dir

    return get_current_topdir(os.path.dirname(dir))
    

def get_topdir():

    topdir = get_current_topdir(os.getcwd())

    if not topdir:
        print >>sys.stderr, "ERROR: current directory is not part of an OpenEmbedded development environment"
        sys.exit(1)

    return topdir


def read_config():
    config = SafeConfigParser()

    if not config.read("conf/oe.conf"):
        print >>sys.stderr, "ERROR: failed to parse %s/conf/oe.conf"%os.getcwd()
        sys.exit(1)

    return config

    
def call(cmd, dry_run=False):
    if type(cmd) == type([]):
        cmdlist = cmd
        cmd = cmdlist[0]
        for arg in cmdlist[1:]:
            cmd = cmd + ' ' + arg

    print "\n>", cmd
    print

    if dry_run:
        return True

    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError, e:
        print >>sys.stderr, e
        return False

    return True
