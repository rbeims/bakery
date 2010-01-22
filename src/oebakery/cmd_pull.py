import os, subprocess, socket, sys, string
import optparse

import oebakery

class PullCommand:

    def __init__(self, config, argv=[]):

        parser = optparse.OptionParser("""Usage: oe pull [options]

  Fetch from and merge with remote repositories.""")

        parser.add_option("-r", "--update-remotes",
                          action="store_true", dest="remotes", default=False,
                          help="update remotes (tracked repositories)")

        parser.add_option("-s", "--pull-submodules",
                          action="store_true", dest="submodules", default=False,
                          help="pull submodule branch head")

        (self.options, self.args) = parser.parse_args(argv)

        self.config = config

        return


    def run(self):

        if not os.path.exists('.git'):
            print 'Aiee!  This is not a git repository!!'
            return

        if not oebakery.call('git pull'):
            print 'Failed to pull updates to main repository'

        if self.options.remotes:
            self.git_remote_update()

        if not self.options.submodules and os.path.exists('.gitmodules'):
            if not oebakery.call('git submodule update --init'):
                print 'Failed to update git submodules'
                return

        # get list of submodules
        submodules = {}
        lines = oebakery.call('git submodule status', quiet=True).split('\n')
        for line in lines:
            if len(line) == 0:
                continue
            path = line[1:].split()[1]
            prefix = line[0]
            commitid = line[1:].split()[0]

            if self.config.has_option('submodules', path):
                url = self.config.get('submodules', path)

                url_split = url.split()
                if len(url_split) < 1 or len(url_split) > 3:
                    print 'Invalid submodule url (%s): %s'%(path, url)
                    return

                if len(url_split) > 1:
                    branch = url_split[1]
                else:
                    branch = None

                if self.options.submodules:
                    self.git_pull_submodule(path, branch)

                if self.options.remotes:
                    self.git_remote_update(path)
        return


    def git_pull_submodule(self, path=None, branch=None):

        if branch == None:
            branch = ''

        if not oebakery.call('git checkout %s'%(branch), dir=path):
            print 'Failed to checkout submodule %s branch %s'%(path, branch)
            return

        if not oebakery.call('git pull', dir=path):
            print 'Failed to pull submodule %s'%(path)
            return

        return


    def git_remote_update(self, path=None):

            # older git versions return 1 on success, and newer versions 0
            # so we will just ignore the return code for now
            oebakery.call('git remote update', dir=path)

            remotes = oebakery.call('git remote', dir=path, quiet=True)
            if remotes:
                for remote in remotes.split('\n'):
                    if not remote or len(remote) == 0:
                        continue
                    if not oebakery.call('git remote prune %s'%(remote),
                                         dir=path):
                        if path == None:
                            path = 'main repository'
                        print 'Failed to prune remote %s in '%(remote, path)

            return
