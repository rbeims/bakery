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

        if self.options.pull and not oebakery.call('git remote update --prune'):
            print 'Failed to update remotes for main repository'

        if os.path.exists('.gitmodules'):
            if not oebakery.call('git submodule update'):
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

    if not os.path.exists(path):

        # create parent dir(s)
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                print '> mkdir -p',parent_dir
                os.makedirs(parent_dir)
            except:
                print 'Failed to add submodule "%s": makedirs failed'%path
                return
        elif parent_dir and not os.path.isdir(parent_dir):
            print 'Failed to add submodule "%s": %s is not a dir'%(
                path, parent_dir)
            return

        if not oebakery.call('git submodule add %s %s'%(url, path)):
            print 'Failed to add submodule "%s"'%path
            return

    if not os.path.exists(os.path.join(path, '.git')):
        if not oebakery.call('git submodule update --init -- %s'%(path)):
            print 'Failed to clone submodule "%s"'%path
            return

    oebakery.chdir(path)

    if not os.path.exists('.git'):
        print 'Bad submodule path: %s not found'%(os.path.join(path, '.git'))
        return

    current_url = oebakery.call('git config --get remote.origin.url',
                                quiet=True).strip()
    if url != current_url:
        if not oebakery.call('git config remote.origin.url %s'%(url)):
            print 'Failed to set origin url for "%s": %s'%(path, url)

    if pull and not oebakery.call('git fetch origin'):
        print 'Failed to fetch updates from origin for "%s"'%path

    if version:
        head_descr = oebakery.call('git describe --all HEAD', quiet=True)

        # check if version is a valid committish object name, and if so,
        # do a checkout
        descr = oebakery.call('git describe --all %s'%version, quiet=True)
        if descr:
            if descr == head_descr:
                # current HEAD is already at the requested version
                pass
            elif not oebakery.call('git checkout %s'%version):
                print 'Failed to checkout revision', version
                return

        else:
            # check if version is a remote branch, and if so, do a checkout
            branch = 'remotes/origin/%s'%version
            descr = oebakery.call('git describe --all %s'%branch, quiet=True)
            if descr:
                if descr == head_descr:
                    # current HEAD is already at the requested branch head
                    pass
                elif not oebakery.call('git checkout %s'%branch):
                    print 'Failed to checkout branch', version
                    return
            else:
                print 'Invalid version for submodule "%s": %s'%(path, version)

    if remotes and len(remotes) > 0:
        for (name, url) in remotes:
            git_update_remote(name, url)

    if pull and not oebakery.call('git remote update --prune'):
        print 'Failed to update remotes for %s'%path

    return
