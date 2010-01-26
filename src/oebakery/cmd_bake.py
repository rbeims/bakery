from __future__ import with_statement # This isn't required in Python 2.6
import oebakery, optparse, ConfigParser, os, re, sys
from oebakery.cmd_tmp import TmpCommand

class BakeCommand:

    def __init__(self, config, argv):

        parser = optparse.OptionParser("""Usage: oe bake [bitbake options]

  Build recipes using BitBake in the current OpenEmbedded development
  environment.  This can be done from any subdirectory of the OpenEmbedded
  development environment.""")

        self.args = argv
        self.config = config

        return


    def run(self):
    
        topdir = oebakery.get_topdir()

        self.tmp_cmd = TmpCommand(self.config)
        tmpdir = self.tmp_cmd.get_tmpdir()

        os.environ['OE_HOME'] = topdir
        os.environ['OE_TMPDIR'] = tmpdir
        os.environ['PATH'] = '%s:%s'%(
            os.path.join(topdir, self.config.get('bitbake', 'path')),
            os.environ['PATH'])
        bbpath = ''
        for path in self.config.get('bitbake', 'bbpath').split(':'):
            bbpath += os.path.normpath(os.path.join(topdir, path)) + ':'
        bbpath = bbpath.strip(':')
        os.environ['BBPATH'] = bbpath

        bb_env_extrawhite = 'OE_HOME OE_TMPDIR'
        if os.getenv('BB_ENV_EXTRAWHITE'):
            os.environ['BB_ENV_EXTRAWHITE'] += " " + bb_env_extrawhite
        else:
            os.environ['BB_ENV_EXTRAWHITE'] = bb_env_extrawhite

        print 'OE_HOME           =', os.environ['OE_HOME']
        print 'OE_TMPDIR         =', os.environ['OE_TMPDIR']
        print 'BBPATH            =', os.environ['BBPATH']
        print 'BB_ENV_EXTRAWHITE =', os.environ['BB_ENV_EXTRAWHITE']
        print ''

        os.umask(022)
        oebakery.call(['bitbake'] + self.args)

        return
