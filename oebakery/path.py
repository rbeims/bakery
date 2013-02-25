import sys
import os
import shutil

from oebakery import *


__topdir = None


def set_topdir(dir):
    global __topdir
    if not (os.path.exists(os.path.join(dir, "conf", "bakery.conf"))):
        logger.critical("Not a valid OE-lite manifest: %s"%dir)
    __topdir = os.path.abspath(dir)
    return __topdir


def get_topdir():
    global __topdir
    if __topdir is None:
        __topdir = locate_topdir()
    return __topdir


def locate_topdir():
    if (os.path.exists(os.path.join(os.getcwd(), 'conf', 'bakery.conf'))):
        # PWD might not be set correctly, so we have to try
        # os.getcwd() first, which is ok as long as we don't recurse
        # into it.  This was experienced when running under Buildbot.
        topdir = os.getcwd()
    else:
        topdir = locate_topdir_recursive(os.getenv('PWD'))
    if not topdir:
        logger.critical("current directory is not part of an OE-lite manifest")
        sys.exit(1)
    return os.path.realpath(topdir)


def locate_topdir_recursive(dir):
    if dir == '/':
        return None
    if (os.path.exists(os.path.join(dir, 'conf', 'bakery.conf'))):
        return os.path.abspath(dir)
    return locate_topdir_recursive(os.path.dirname(dir))


def chdir(dir, quiet=False):
    logger.debug("chdir: %s", dir)
    try:
        cwd = os.getcwd()
    except OSError, e:
        cwd = None
    if (cwd and
        os.path.realpath(os.path.normpath(dir)) == os.path.normpath(cwd)):
        return

    if not quiet:
        print '> cd', dir

    os.chdir(dir)

    return


def copy_local_conf_sample(confdir):
    config = os.path.join(confdir, 'local.conf')
    sample = os.path.join(confdir, 'local.conf.sample')
    if not os.path.exists(config) and os.path.exists(sample):
        print '> cp %s %s'%(sample, config)
        try:
            shutil.copyfile(sample, config)
        except Exception, e:
            logger.warning("failed to write config file: %s: %s", config, e)
