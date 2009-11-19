import os, subprocess, socket, sys, string
import optparse

import oebakery

class UpdateCommand:

    def __init__(self, config, argv=[]):

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
                git_update_remote(name, url)

        if self.options.pull:
            # older git versions return 1 on success, and newer versions 0
            # so we will just ignore the return code for now
            oebakery.call('git remote update')

        if self.options.pull and self.config.has_section('remotes'):
            for (name, url) in self.config.items('remotes'):
                if not oebakery.call('git remote prune %s'%(name)):
                    print 'Failed to prune remotes for main repository'

        if os.path.exists('.gitmodules'):
            if not oebakery.call('git submodule update --init'):
                print 'Failed to update git submodules'
                return

        if self.config.has_section('submodules'):

            for (path, url) in self.config.items('submodules'):

                if url.find(' ') >= 0:
                    (url, version) = string.rsplit(url, maxsplit=1)
                else:
                    version = None

                section_name = 'remotes "%s"'%path
                if self.config.has_section(section_name):
                    remotes = self.config.items(section_name)
                else:
                    remotes = None

                git_update_submodule(path, url, version, remotes,
                                              self.options.pull)

        return


def git_update_remote(name, url):

    # fetch list of remotes
    remotes_list = oebakery.call('git remote -v', quiet=True).split('\n')
    remotes = {}
    for remote in remotes_list:
        if '\t' in remote:
            (iter_name, iter_url) = string.split(remote, '\t', maxsplit=1)
            remotes[iter_name] = iter_url

    # if matching remote is found, do nothing and return
    if remotes.has_key(name) and remotes[name] == url:
        return

    # if remote is found, but with different url, change url and return
    if remotes.has_key(name):
        oebakery.call('git config remote.%s.url %s'%(name, url))
        return

    # if another remote is found with same url, rename it and return
    	# generally seems like a bad idea, so let's not do that...

    if not oebakery.call('git remote add %s %s'%(name, url)):
        print 'Failed to add remote "%s"'%name
        return

    return


def git_update_submodule(path, url, version=None, remotes=None, pull=False):

    oebakery.chdir(oebakery.get_topdir())

    pristine_clone = False
    if not os.path.exists(os.path.join(path, '.git')):

        # git clone
        if version:
            if not oebakery.call('git clone -n %s %s'%(url, path)):
                print 'Failed to clone submodule %s'%path
                return
            pristine_clone = True
        else:
            if not oebakery.call('git clone %s %s'%(url, path)):
                print 'Failed to clone submodule %s'%path
                return

    oebakery.chdir(path)

    # update origin url if necessary
    current_url = oebakery.call('git config --get remote.origin.url',
                                quiet=True).strip()
    if url != current_url:
        if not oebakery.call('git config remote.origin.url %s'%(url)):
            print 'Failed to set origin url for "%s": %s'%(path, url)

    # fetch updates from origin
    if pull and not oebakery.call('git fetch origin'):
        print 'Failed to fetch updates from origin for "%s"'%path

    if version:

        # check if version is a valid commit or remote branch name
        commit = branch = False
        descr = oebakery.call('git describe --all %s'%version, quiet=True)
        if descr:
            commit = descr
        else:
            branch = 'remotes/origin/%s'%version
            if oebakery.call('git describe --all %s'%branch, quiet=True):
                pass
            else:
                print 'Error: invalid version for submodule %s: %s'%(
                    path, version)
                return
    
        # create and checkout local branch tracking the requested remote branch
        if branch:
            if not oebakery.call('git checkout --track -b %s %s'%(
                    version, branch)):
                print 'Failed to create local tracking branch for', branch
                return
    
        # checkout the requested version (specific commit, or local branch)
        elif (pristine_clone or
              commit != oebakery.call('git describe --all HEAD', quiet=True)):
            if not oebakery.call('git checkout %s'%version):
                print 'Failed to checkout', version
                return

    if remotes and len(remotes) > 0:
        for (name, url) in remotes:
            git_update_remote(name, url)

    # older git versions return 1 on success, and newer versions 0
    # so we will just ignore the return code for now
    oebakery.call('git remote update')

    if pull and remotes and len(remotes) > 0:
        for (name, url) in remotes:
            if not oebakery.call('git remote prune %s'%(name)):
                print 'Failed to prune remotes for %s'%path

    return
