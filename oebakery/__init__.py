from __future__ import with_statement # This isn't required in Python 2.6

__version__ = "0.5"

__all__ = [

    "get_topdir",
    "read_config",
    "call",

]

import sys, os, subprocess, re, ConfigParser


def get_current_topdir(dir):

    if dir == "/":
        return None

    if (os.path.exists("%s/conf/bakery.ini"%dir) and
        os.path.exists("%s/bitbake/.git"%dir)):
        return dir

    return get_current_topdir(os.path.dirname(dir))
    

def get_topdir():

    topdir = get_current_topdir(os.getenv('PWD'))

    if not topdir:
        print >>sys.stderr, "ERROR: current directory is not part of an OE Bakery development environment"
        sys.exit(1)

    return topdir


def read_config():
    config = ConfigParser.SafeConfigParser()

    if not config.read("conf/bakery.ini"):
        print >>sys.stderr, "ERROR: failed to parse %s/conf/bakery.ini"%os.getcwd()
        sys.exit(1)


    if not config.has_section("bitbake"):
        print "WARNING: no [bitbake] section in conf/bakery.ini"
        config.add_section("bitbake")
    if not config.has_option("bitbake", "repository"):
        config.set("bitbake", "repository",
                   "git://git.openembedded.org/bitbake")
    if not config.has_option("bitbake", "version"):
        config.set("bitbake", "version", "tags/1.8.12")
    if not config.has_option("bitbake", "origin"):
        config.set("bitbake", "origin", "origin")

    if not config.has_section("metadata"):
        print "WARNING: no [metadata] section in conf/bakery.ini"
        config.add_section("metadata")
    if not config.has_option("metadata", "repository"):
        config.set("metadata", "repository",
                   "git://git.openembedded.org/openembedded")
    if not config.has_option("metadata", "directory"):
        config.set("metadata", "directory", "metadata")
    if not config.has_option("metadata", "origin"):
        config.set("metadata", "origin", "origin")
    for option in config.options("metadata"):
        if (len(option) > len("remote.") and
            option[:len("remote.")] == "remote." and
            option[len("remote."):] in ["bin", "lib", "conf", "bitbake",
                                        "ingredient", "prebake", "tmp", "scm"]):
                print >>sys.stderr, "WARNING: Invalid remote option %s"%option
                config.remote_option("metadata",option)

    return config


def get_simple_config_line(filename, variable):
    if os.path.exists(filename):
        regex = re.compile(variable +'\s*=\s*[\"\'](.*)[\"\']')
        with open(filename) as file:
            for line in file.readlines():
                match = regex.match(line)
                if match:
                    return match.group(1)
    return None

    
def call(cmd, dry_run=False):
    if type(cmd) == type([]):
        cmdlist = cmd
        cmd = cmdlist[0]
        for arg in cmdlist[1:]:
            cmd = cmd + ' ' + arg

    print "\n>", cmd

    if dry_run:
        return True

    try:
        subprocess.check_call(cmd, shell=True, stdin=sys.stdin)
    except subprocess.CalledProcessError, e:
        print >>sys.stderr, e
        return False

    return True


#def fetch_file(file):
#
#    colon = file.find(':')
#
#    if colon == -1:
#        print "file is local path"
#        return shutil.copyfile(self.file, "conf/bakery.ini")
#
#    elif file[:colon] in ['http', 'ftp', 'https']:
#        print "use wget"
#        return oebakery.call("wget -O conf/bakery.ini %s"%(file))
#
#    elif self.file[:colon] in ['ssh']:
#        print "use scp (fall through)"
#        file = file[colon+3:]
#
#    elif file[colon+1:colon+3] == '//':
#        print "invalid url"
#        return
#
#    print "use scp"
#    bakery.call("scp %s conf/bakery.ini"%(file))
#
#    return
