from __future__ import with_statement # This isn't required in Python 2.6

__version__ = '0.5'

__all__ = [

    'set_topdir',
    'locate_topdir',
    'get_topdir',
    'read_config',
    'call',

]

import sys, os, subprocess, re, ConfigParser, string, shutil


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

    if not config.has_section('tmp'):
        config.add_section('tmp')
    if not config.has_option('tmp', 'tmpdir'):
        config.set('tmp', 'tmpdir', 'tmp')
    if not config.has_option('tmp', 'default'):
        config.set('tmp', 'default', 'default')

    if not config.has_section('bitbake'):
        config.add_section('bitbake')
    if not config.has_option('bitbake', 'path'):
        config.set('bitbake', 'path', 'bitbake/bin')
    if not config.has_option('bitbake', 'bbpath'):
        config.set('bitbake', 'bbpath', '')
    if not config.has_option('bitbake', 'confdir'):
        config.set('bitbake', 'confdir', 'conf')

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


def call(cmd, dir=None, quiet=False, success_returncode=0):

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
        if process.returncode == success_returncode:
            retval = output

    else:
        returncode = subprocess.call(cmd, shell=True, stdin=sys.stdin)
        if returncode == success_returncode:
            retval = True

    if dir:
        chdir(pwd, quiet)

    return retval


def chdir(dir, quiet=False):
    if os.path.realpath(os.path.normpath(dir)) == os.path.normpath(os.getcwd()):
        return

    if not quiet:
        print '> cd', dir

    os.chdir(dir)

    return


def copy_local_conf_sample(confdir):
    
    config = os.path.join(confdir, 'local.conf')
    sample = os.path.join(confdir, 'local.conf.sample')
    if not os.path.exists(config) and os.path.exists(sample):
        try:
            print '> cp %s %s'%(sample, config)
            shutil.copyfile(sample, config)
        except:
            print 'Warning: failed to write config file:', config


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
