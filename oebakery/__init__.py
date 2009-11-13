from __future__ import with_statement # This isn't required in Python 2.6

__version__ = "0.5"

__all__ = [

    "get_topdir",
    "read_config",
    "git_add_remote",
    "git_add_submodule",
    "call",

]

import sys, os, subprocess, re, ConfigParser, string


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

    if not os.path.exists(".bakery"):
        print >>sys.stderr, "ERROR: no .bakery in current directory"
        sys.exit(1)
    if not config.read(".bakery"):
        print >>sys.stderr, "ERROR: failed to .bakery"
        sys.exit(1)

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


def git_add_remote(name, url):

    if not call("git remote add %s %s"%(name, url)):
        print 'Failed to add remote "%s"'%name
        return

    return


def git_add_submodule(path, url, remotes=None):

    if os.path.exists(path):
        print 'Failed to add submodule "%s": path exists'%path
        return

    parent_dir = os.path.dirname(path)
    if parent_dir and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir)
        except:
            print 'Failed to add submodule "%s": makedirs failed'%path
            return
    elif parent_dir and not os.path.isdir(parent_dir):
        print 'Failed to add submodule "%s": %s is not a dir'%(path, parent_dir)
        return

    if url.find(' ') >= 0:
        (url, branch) = string.rsplit(url, maxsplit=1)
        branch = '-b %s '%branch
    else:
        branch = ''

    if not call("git submodule add %s%s %s"%(branch, url, path)):
        print 'Failed to add submodule "%s"'%path
        return

    if remotes and len(remotes) > 0:
        pwd = os.environ['PWD']
        os.chdir(path)
        for (name, url) in remotes:
            git_add_remote(name, url)
        os.chdir(pwd)

    return
    
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
