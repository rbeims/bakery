import os, subprocess, socket, sys, string
import optparse

import oebakery

class UpdateCommand:

    def __init__(self, config, argv=[]):

        parser = optparse.OptionParser("""Usage: oe update [options]

  Update OE Bakery development environment in the current directory.""")

        (self.options, self.args) = parser.parse_args(argv)

        self.config = config

        return


    def run(self):

        if not os.path.exists('.git'):
            print 'Aiee!  This is not a git repository!!'
            return

        if self.config.has_section('remotes'):
            for (name, url) in self.config.items('remotes'):
                git_update_remote(name, url)

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
                    branch = url_split[1]
                else:
                    branch = None

                if len(url_split) > 2:
                    push_url = url_split[2]
                else:
                    push_url = None

                section_name = 'remotes "%s"'%path
                if self.config.has_section(section_name):
                    remotes = self.config.items(section_name)
                else:
                    remotes = None

                git_update_submodule(path, fetch_url, push_url, branch, remotes)

        return


def git_update_remote(name, url, path=None):

    url_split = url.split()
    if len(url_split) < 1 or len(url_split) > 2:
        print 'Invalid remote url:',url
        return
    if len(url_split) == 2:
        push_url = url_split[1]
    else:
        push_url = None
    fetch_url=url_split[0]

    # get list of remotes and their urls
    remotes_list = oebakery.call('git remote -v', dir=path, quiet=True)
    if remotes_list == None:
        print 'Failed to get list of remotes', remotes_list
        return
    else:
        remotes_list = remotes_list.split('\n')

    # get fetch urls
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
                                 dir=path, quiet=True)
        if iter_url:
            remotes_push[iter_name] = iter_url.strip()

    # if remote is not found, add it and return
    if not remotes_fetch.has_key(name):
        if not oebakery.call('git remote add %s %s'%(name, fetch_url),
                             dir=path):
            print 'Failed to add remote', name
            return
        # also add push url if specified
        if push_url:
            oebakery.call('git config remote.%s.pushurl %s'%(name, push_url),
                          dir=path)
        return

    # change (fetch) url if not matching
    if remotes_fetch[name] != fetch_url:
        oebakery.call('git config remote.%s.url %s'%(name, fetch_url),
                      dir=path)

    # if push url is different url, change it
    if push_url:
        if not remotes_push.has_key(name) or remotes_push[name] != push_url:
            oebakery.call('git config remote.%s.pushurl %s'%(name, push_url),
                          dir=path)

    # if push url is currently set, but shouldn't be, remove it
    else:
        if remotes_push.has_key(name) and remotes_push[name] != fetch_url:
            oebakery.call('git config --unset remote.%s.pushurl'%(name),
                          dir=path)

    return


def git_submodule_status(path):

    for line in oebakery.call('git submodule status', quiet=True).split('\n'):
        if len(line) == 0:
            continue

        if (path == line[1:].split()[1]):
            prefix = line[0]
            commitid = line[1:].split()[0]
            return (prefix, commitid)

    return None


def git_update_submodule(path, fetch_url, push_url=None, branch=None,
                         remotes=None):

    status = git_submodule_status(path)

    # Add as git submodule if necessary
    if (status is None):

        if not oebakery.call('git submodule add %s %s'%(fetch_url, path)):
            print 'Failed to add submodule %s'%path
            return

        if not oebakery.call('git submodule init %s'%(path)):
            print 'Failed to init submodule %s'%path
            return

    # set push_default to 'tracking' if unset
    push_default = oebakery.call('git config --get push.default',
                                 dir=path, quiet=True)
    if (push_default == None):
        oebakery.call('git config push.default tracking', dir=path)

    # update origin fetch url if necessary
    current_url = oebakery.call('git config --get remote.origin.url',
                                dir=path, quiet=True)
    if current_url:
        current_url = current_url.strip()
    if fetch_url != current_url:
        if not oebakery.call('git config remote.origin.url %s'%(fetch_url),
                             dir=path):
            print 'Failed to set origin url for "%s": %s'%(path, fetch_url)

    # set push url as specified in bakery.ini
    current_url = oebakery.call('git config --get remote.origin.pushurl',
                                dir=path, quiet=True)
    if current_url:
        current_url = current_url.strip()
    if push_url and current_url != push_url:
        if not oebakery.call('git config remote.origin.pushurl %s'%(push_url),
                             dir=path):
            print 'Failed to set origin push url for "%s": %s'%(path, push_url)

    # remove override of push url if not specified in bakery.ini
    if not push_url and current_url:
        if not oebakery.call('git config --unset remote.origin.pushurl',
                             dir=path):
            print 'Failed to unset origin push url for "%s"'%(path)

    # update remotes
    if remotes and len(remotes) > 0:
        for (name, url) in remotes:
            git_update_remote(name, url, path=path)

    return
