import optparse, sys, os
import subprocess, socket, string
import oebakery
from oebakery import die, err

arguments = None
description = """Update OE-lite development environment"""

def run(parser, options, args, config=None):
    ok = True

    if not os.path.exists('.git'):
        die("Aiee!  This is not a git repository!!")

    OE_REMOTES = config["OE_REMOTES"] or ""
    remotes = []
    if OE_REMOTES:
        for remote in OE_REMOTES.split():
            url = config["OE_REMOTE_"+remote]
            if not url:
                err("OE_REMOTE_%s must be defined"%(remote))
                ok = False
            remotes.append((remote, url))

    OE_MODULES = config["OE_MODULES"]
    submodules = []
    #submodule_remotes = {}
    if OE_MODULES:

        for submodule in OE_MODULES.split():

            path = config["OE_MODULE_PATH_" + submodule]
            url = config["OE_MODULE_URL_" + submodule]
            pushurl = config["OE_MODULE_PUSHURL_" + submodule]
            branch = config["OE_MODULE_BRANCH_" + submodule]

            if not path:
                path = "meta/" + submodule
            if not url:
                err("OE_MODULE_URL_%s most be defined"%(submodule))
                ok = False
            if not branch:
                branch = "HEAD"

            #submodule_remotes[submodule] = []
            submodule_remotes = []
            varname = "OE_MODULE_REMOTES_" + submodule
            OE_MODULE_REMOTES = config[varname] or ""
            for remote in OE_MODULE_REMOTES.split():
                varname = "OE_MODULE_REMOTE_%s_%s"%(submodule, remote)
                remote_url = config[varname]
                if not url:
                    err("%s must be defined"%(varname))
                    ok = False
                #submodule_remotes[submodule].append((remote, url))
                submodule_remotes.append((remote, remote_url))

            submodules.append((path, url, pushurl, branch, submodule_remotes))

    if not ok:
        die("OE-lite configuration error(s)")

    for (name, url) in remotes:
        if not git_update_remote(name, url):
            err("update of remote %s failed"%(name))
            ok = False

    if os.path.exists('.gitmodules'):
        if not oebakery.call('git submodule init'):
            die("Failed to initialize git submodules")
        if not oebakery.call('git submodule update'):
            die("Failed to update git submodules")

    for submodule in submodules:
        #if not git_update_submodule(*submodule):
        retval = git_update_submodule(*submodule)
        if not retval:
            err("update of submodule %s failed"%(submodule[0]))
            ok = False

    if not ok:
        err("update failed")
        return 1

    return 0


def git_update_remote(name, url, path=None):
    ok = True

    url_split = url.split()
    if len(url_split) < 1 or len(url_split) > 2:
        err("Invalid remote url: %s"%(url))
        return False
    if len(url_split) == 2:
        push_url = url_split[1]
    else:
        push_url = None
    fetch_url=url_split[0]

    # get list of remotes and their urls
    remotes_list = oebakery.call('git remote -v', dir=path, quiet=True)
    if remotes_list == None:
        err("Failed to get list of remotes")
        return False
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
            err("Failed to add remote %s"%(name))
            return False
        # also add push url if specified
        if push_url:
            if not oebakery.call(
                'git config remote.%s.pushurl %s'%(name, push_url),
                                 dir=path):
                err("failed to set pushurl %s for %s"%(push_url, name))
                ok = False
        return True

    # change (fetch) url if not matching
    if remotes_fetch[name] != fetch_url:
        if not oebakery.call('git config remote.%s.url %s'%(name, fetch_url),
                             dir=path):
            err("failed to set url %s for %s"%(name, fetch_url))
            ok = False

    # if push url is different url, change it
    if push_url:
        if not remotes_push.has_key(name) or remotes_push[name] != push_url:
            if not oebakery.call(
                'git config remote.%s.pushurl %s'%(name, push_url),
                dir=path):
                err("failed to set pushurl %s for %s"%(push_url, name))
                ok = False

    # if push url is currently set, but shouldn't be, remove it
    else:
        if remotes_push.has_key(name) and remotes_push[name] != fetch_url:
            if not oebakery.call('git config --unset remote.%s.pushurl'%(name),
                                 dir=path):
                err("failed to unset pushurl for %s"%(name))
                ok = False

    return True


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
    ok = True

    status = git_submodule_status(path)

    print >>sys.stderr, "git_update_submodule: path=%s fetch_url=%s"%(path, fetch_url)

    # Add as git submodule if necessary
    if (status is None):

        if not oebakery.call('git submodule add %s %s'%(fetch_url, path)):
            err("Failed to add submodule %s"%(path))
            return False

        if not oebakery.call('git submodule init %s'%(path)):
            err("Failed to init submodule %s"%(path))
            return False

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
            err("Failed to set origin url %s for %s"%(fetch_url, path))
            ok = False

    # set push url as specified
    current_url = oebakery.call('git config --get remote.origin.pushurl',
                                dir=path, quiet=True)
    if current_url:
        current_url = current_url.strip()
    if push_url and current_url != push_url:
        if not oebakery.call('git config remote.origin.pushurl %s'%(push_url),
                             dir=path):
            err("Failed to set origin push url %s for %s"%(push_url, path))
            ok = False

    # remove override of push url if not specified
    if not push_url and current_url:
        if not oebakery.call('git config --unset remote.origin.pushurl',
                             dir=path):
            err("Failed to unset origin push url for %s"%(path))
            ok = False

    # update remotes
    if remotes and len(remotes) > 0:
        for (name, url) in remotes:
            if not git_update_remote(name, url, path=path):
                err("update of remote %s failed"%(name))
                ok = False

    return ok
