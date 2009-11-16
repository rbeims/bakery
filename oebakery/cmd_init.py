import os, subprocess, socket, shutil, optparse
import oebakery
from oebakery.cmd_update import UpdateCommand

class InitCommand:

    def __init__(self, argv=[]):

        parser = optparse.OptionParser("""Usage: oe init [options]

  Setup OE Bakery development environment in the current directory.""")

        (self.options, self.args) = parser.parse_args(argv)

        self.config = oebakery.read_config()

        return


    def run(self):

        topdir = oebakery.set_topdir(os.path.curdir)

        if not os.path.exists('.git'):

            if not oebakery.call('git init'):
                print 'Failed to initialize git'
                return

            if not oebakery.call('git config push.default tracking'):
                print 'Failed to set push.default = tracking'

        oebakery.copy_local_conf_sample(self.config.get('bitbake', 'confdir'))

        self.update_cmd = UpdateCommand(self.config)
        return self.update_cmd.run()
