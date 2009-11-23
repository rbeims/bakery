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

                url_split = url.split()
                if len(url_split) < 1 or len(url_split) > 3:
                    print 'Invalid submodule url (%s): %s'%(path, url)
                    return

                fetch_url = url_split[0]

                if len(url_split) > 1:
                    version = url_split[1]
                else:
                    version = None

                if len(url_split) > 2:
                    push_url = url_split[2]
                else:
                    push_url = None

                section_name = 'remotes "%s"'%path
                if self.config.has_section(section_name):
                    remotes = self.config.items(section_name)
                else:
                    remotes = None

                git_update_submodule(path, fetch_url, push_url, version,
                                     remotes, self.options.pull)

        return


def git_update_remote(name, url):

    url_split = url.split()
    if len(url_split) < 1 or len(url_split) > 2:
        print 'Invalid remote url:',url
        return
    if len(url_split) == 2:
        push_url = url_split[1]
    else:
        push_url = None
    fetch_url=url_split[0]

    # git list of remotes and their fetch urls
    remotes_list = oebakery.call('git remote -v', quiet=True).split('\n')

    
    remotes_list = oebakery.call('git remote -v', quiet=True)
    if remotes_list == None:
        print 'Failed to get list of remotes', remotes_list
        return
    else:
        remotes_list = remotes_list.split('\n')

    remotes_fetch = {}
    for remote in remotes_list:
        if '\t' in remote:
            (iter_name, iter_url) = string.split(remote, '\t', maxsplit=1)
            if iter_url[-8:] == ' (fetch)':
                remotes_fetch[iter_name] = iter_url[:-8]
            elif iter_url[-7:] == ' (push)':
                # don't take push url here, but use git config to know
                # if it is actually set, or just derived from fetch url
                pass
            else:
                # pre git-1.6.4 did only have fetch url's
                remotes_fetch[iter_name] = iter_url

    # get push urls
    remotes_push = {}
    for iter_name in remotes_fetch.keys():
        iter_url = oebakery.call('git config --get remote.%s.pushurl'%iter_name,
                                 quiet=True)
        if iter_url:
            remotes_push[iter_name] = iter_url.strip()

    # if remote is not found, add it and return
    if not remotes_fetch.has_key(name):
        if not oebakery.call('git remote add %s %s'%(name, fetch_url)):
            print 'Failed to add remote', name
            return
        # also add push url if specified
        if push_url:
            oebakery.call('git config remote.%s.pushurl %s'%(name, push_url))
        return

    # change (fetch) url if not matching
    if remotes_fetch[name] != fetch_url:
        oebakery.call('git config remote.%s.url %s'%(name, fetch_url))

    # if push url is different url, change it
    if push_url:
        if not remotes_push.has_key(name) or remotes_push[name] != push_url:
            oebakery.call('git config remote.%s.pushurl %s'%(name, push_url))

    # if push url is currently set, but shouldn't be, remove it
    else:
        if remotes_push.has_key(name) and remotes_push[name] != fetch_url:
            oebakery.call('git config --unset remote.%s.pushurl'%(name))

    return


def git_update_submodule(path, fetch_url, push_url=None, version=None,
                         remotes=None, pull=False):

    oebakery.chdir(oebakery.get_topdir())

    pristine_clone = False
    if not os.path.exists(os.path.join(path, '.git')):

        # git clone
        if version:
            if not oebakery.call('git clone -n %s %s'%(fetch_url, path)):
                print 'Failed to clone submodule %s'%path
                return
            pristine_clone = True

        else:
            if not oebakery.call('git clone %s %s'%(fetch_url, path)):
                print 'Failed to clone submodule %s'%path
                return

        oebakery.chdir(path)

        if push_url:
            oebakery.call('git config remote.origin.pushurl %s'%(push_url))

        oebakery.call('git config push.default tracking')

    else:
        oebakery.chdir(path)

    # update origin fetch url if necessary
    current_url = oebakery.call('git config --get remote.origin.url',
                                quiet=True)
    if current_url:
        current_url = current_url.strip()
    if fetch_url != current_url:
        if not oebakery.call('git config remote.origin.url %s'%(fetch_url)):
            print 'Failed to set origin url for "%s": %s'%(path, fetch_url)

    current_url = oebakery.call('git config --get remote.origin.pushurl',
                                quiet=True)
    if current_url:
        current_url = current_url.strip()

    # set push url as specified in bakery.ini
    if push_url and current_url != push_url:
        if not oebakery.call('git config remote.origin.pushurl %s'%(push_url)):
            print 'Failed to set origin push url for "%s": %s'%(path, push_url)

    # remove override of push url if not specified in bakery.ini
    if not push_url and current_url:
        if not oebakery.call('git config --unset remote.origin.pushurl'):
            print 'Failed to set origin push url for "%s": %s'%(path, push_url)

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
