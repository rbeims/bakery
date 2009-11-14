from __future__ import with_statement # This isn't required in Python 2.6

__version__ = '0.5'

__all__ = [

    'set_topdir',
    'locate_topdir',
    'get_topdir',
    'read_config',
    'git_update_remote',
    'git_update_submodule',
    'call',

]

import sys, os, subprocess, re, ConfigParser, string


TOPDIR = None

def set_topdir(dir):
    global TOPDIR

    if not (os.path.exists(os.path.join(dir, 'bakery.ini'))
            or os.path.exists(os.path.join('.bakery'))):
        print >>sys.stderr, 'ERROR: not a valid OE Bakery development environment:', dir
        return None

    TOPDIR = os.path.abspath(dir)

    return TOPDIR
    

def locate_topdir():
    global TOPDIR

    TOPDIR = locate_topdir_recursive(os.getenv('PWD'))

    if not TOPDIR:
        print >>sys.stderr, 'ERROR: current directory is not part of an OE Bakery development environment'
        sys.exit(1)

    return TOPDIR


def locate_topdir_recursive(dir):

    if dir == '/':
        return None

    if (os.path.exists('%s/bakery.ini'%dir) or os.path.exists('%s/.bakery'%dir)):
        return os.path.abspath(dir)

    return locate_topdir_recursive(os.path.dirname(dir))


def get_topdir():
    global TOPDIR
    return TOPDIR


def read_config():
    config = ConfigParser.SafeConfigParser()

    if os.path.exists('bakery.ini'):
        inifile = 'bakery.ini'
    elif os.path.exists('.bakery'):
        inifile = '.bakery'
    else:
        print >>sys.stderr, 'ERROR: no bakery.ini or .bakery in current directory'
        sys.exit(1)

    if not config.read(inifile):
        print >>sys.stderr, 'ERROR: failed to read %s'%inifile
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


def git_update_remote(name, url):

    # fetch list of remotes

    # if matching remote is found, do nothing and return

    # if remote is found, but with different url, change url and return

    # if another remote is found with same url, rename it and return

    if not call('git remote add %s %s'%(name, url)):
        print 'Failed to add remote "%s"'%name
        return

    return


def git_update_submodule(path, url, branch=None, remotes=None, pull=False):

    chdir(get_topdir())

    if not os.path.exists(path):

        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                print '> mkdir -p',parent_dir
                os.makedirs(parent_dir)
            except:
                print 'Failed to add submodule "%s": makedirs failed'%path
                return
        elif parent_dir and not os.path.isdir(parent_dir):
            print 'Failed to add submodule "%s": %s is not a dir'%(path, parent_dir)
            return

        if branch:
            branch_arg = '-b %s '%branch
        else:
            branch_arg = ''

        if not call('git submodule add %s%s %s'%(branch_arg, url, path)):
            print 'Failed to add submodule "%s"'%path
            return

        branch = None

    chdir(path)

    if branch:
        if not call('git checkout -b %s remotes/origin/%s'%(branch, branch)):
            print 'Failed to checkout new branch: %s'%branch
            return

    if not os.path.exists('.git'):
        print 'Bad submodule path: %s not found'%(os.path.join(path, '.git'))
        return

    if not call('git config remote.origin.url %s'%(url), ):
        print 'Failed to set origin url for "%s": %s'%(path, url)

    if pull and not call('git pull'):
        print 'Failed to pull updates to %s'%path

    if remotes and len(remotes) > 0:
        for (name, url) in remotes:
            git_update_remote(name, url)

    if pull and not call('git remote update --prune'):
        print 'Failed to update remotes for %s'%path

    return

    
def call(cmd, dir=None, quiet=False):

    if type(cmd) == type([]):
        cmdlist = cmd
        cmd = cmdlist[0]
        for arg in cmdlist[1:]:
            cmd = cmd + ' ' + arg

    if dir:
        pwd = os.getcwd()
        chdir(dir, quiet)

    if not quiet:
        print '>', cmd

    retval = None
    if quiet:
        process = subprocess.Popen(cmd, shell=True, stdin=sys.stdin,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        output = process.communicate()[0]
        if process.returncode == 0:
            retval = output
    else:
        returncode = subprocess.call(cmd, shell=True, stdin=sys.stdin)
        if returncode == 0:
            retval = True

    if dir:
        chdir(pwd, quiet)

    return retval


def chdir(dir, quiet=False):
    if os.path.abspath(dir) == os.path.abspath(os.getcwd()):
        return

    if not quiet:
        print '> cd', dir

    os.chdir(dir)

    return


#def fetch_file(file):
#
#    colon = file.find(':')
#
#    if colon == -1:
#        print 'file is local path'
#        return shutil.copyfile(self.file, 'conf/bakery.ini')
#
#    elif file[:colon] in ['http', 'ftp', 'https']:
#        print 'use wget'
#        return call('wget -O conf/bakery.ini %s'%(file))
#
#    elif self.file[:colon] in ['ssh']:
#        print 'use scp (fall through)'
#        file = file[colon+3:]
#
#    elif file[colon+1:colon+3] == '//':
#        print 'invalid url'
#        return
#
#    print 'use scp'
#    bakery.call('scp %s conf/bakery.ini'%(file))
#
#    return
