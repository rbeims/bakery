import os, subprocess, socket, sys, string
import optparse

import oebakery

class UpdateCommand:

    def __init__(self, config, argv=None):

        parser = optparse.OptionParser("""Usage: oe update [options]

  Update OE Bakery development environment in the current directory.""")

        parser.add_option("-p", "--pull",
                          action="store_true", dest="pull", default=False,
                          help="pull from remote repositories")

        (self.options, self.args) = parser.parse_args(argv)

        self.config = config

        return


    def run(self):

        if not os.path.exists('.git'):
            print 'Aiee!  This is not a git repository!!'
            return

        if self.options.pull and not oebakery.call('git pull'):
            print 'Failed to pull updates to main repository'

        if self.config.has_section('remotes'):
            for (name, url) in self.config.items('remotes'):
                oebakery.git_update_remote(name, url)

        if self.options.pull and not oebakery.call('git remote update --prune'):
            print 'Failed to update remotes for main repository'

        if os.path.exists('.gitmodules'):
            if not oebakery.call('git submodule update --init'):
                print 'Failed to update git submodules'
                return

        if self.config.has_section('submodules'):

            for (path, url) in self.config.items('submodules'):

                if url.find(' ') >= 0:
                    (url, branch) = string.rsplit(url, maxsplit=1)
                else:
                    branch = None

                section_name = 'remotes "%s"'%path
                if self.config.has_section(section_name):
                    remotes = self.config.items(section_name)
                else:
                    remotes = None

                oebakery.git_update_submodule(path, url, branch, remotes,
                                              self.options.pull)

        return
