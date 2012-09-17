import os
import string

import oebakery
from oebakery import die, err

# oe update: (setup submodules based on OETASK in bakery.conf)
#   git submodule sync
#   git submodule add $url $path for missing submodules
#     and: git submodule update --init --recursive $path
#   change bakery repo .gitmodules submodule.$submodule.url if not right
#   change submodule repo .git/config remote.origin.url if not right
#     (or will this automagically be done by next submodule sync???)
#   change submodule repo .git/config remote.origin.pushurl if not right
#   if submodule is tracking a branch:
#     if local $branch does not exist:
#       git branch --track $branch origin/$branch
#     elif submodule repo .git/config branch.$branch.merge != refs/heads/$branch:
#       git branch --set-upstream $branch origin/$branch
#   git submodule sync
#   print warning for submodules not in OETASK
#     (ask to add it to bakery.conf or remove it)
#         
#

# oe pull:
#   git pull in bakery repo
#   oe init
#   foreach module in OESTACK:
#     check submodule status
#     if submodule is missing:
#       print error message, and skip submodule
#     if HEAD is not in a local or remote branch:
#       print error message, and skip submodule
#     if submodule is tracking a branch: (ie. ;branch=something in OESTACK)
#       if $branch is not checked out:
#         git checkout $branch
#       git pull in the submodule
#     else:
#       git submodule update --recursive
#

arguments = None
description = "Update OE-lite repository according to configuration"


def run(parser, options, args, config):
    if not os.path.exists('.git'):
        die("Aiee! This is not even a git repository:", os.getcwd())

    # check for possibly detached heads, and abort (return False)
    # if this or at least one of the submodules looks detached

    paths = []
    submodules = []
    for path, url, params in config["__submodules"]:
        if not args or path in args:
            paths.append(path)
            submodules.append((path, url, params))

    return not update_submodules(submodules)


def update_submodules(submodules):
    ok = True
    for path, url, params in submodules:
        if not check_submodule(path):
            err("submodule %s is not on a branch"%(path))
            ok = False
            continue
        if not update_submodule(path, url, params):
            err("update of submodule %s failed"%(path))
            ok = False

    if not ok:
        err("update failed")
        return False

    return True


def check_submodule(path):
    if not os.path.exists(path):
        return True
    branches = git_branch_status(path, options="-a --contains HEAD")
    return len(branches) > 0

def update_submodule(path, fetch_url, params):
    push_url = params.get("push", None)
    ok = True

    if (os.path.exists(path) and
        not oebakery.call("git submodule sync -- %s"%(path))):
        err("Failed to synchronize git submodule")

    status = git_submodule_status(path)
    if status and status[0] == "-":
        cmd = "git submodule update --init --recursive"
        if not oebakery.call("%s %s"%(cmd, path)):
            err("Failed to add submodule: %s"%(path))
            return False

    elif status is None:
        cmd = "git submodule add -f"
        if "branch" in params:
            branch = params["branch"]
            if branch != "master":
                cmd += " -b %s"%(params["branch"])
        if not oebakery.call("%s -- %s %s"%(cmd, fetch_url, path)):
            err("Failed to add submodule: %s"%(path))
            return False
        if not oebakery.call(
            "git submodule update --init --recursive %s"%(path)):
            err("Failed to initialize submodule: %s"%(path))
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

    if not oebakery.call('git remote update --prune origin', dir=path):
        err("failed to update remote origin")
        ok = False

    # remove override of push url if not specified
    if not push_url and current_url:
        if not oebakery.call('git config --unset remote.origin.pushurl',
                             dir=path):
            err("Failed to unset origin push url for %s"%(path))
            ok = False

    # update remotes
    for (name, url) in params.get("remote", []):
        if not git_update_remote(name, url, path=path):
            err("update of remote %s failed"%(name))
            ok = False

    # 
    if "tag" in params:
        tag = params["tag"]
        if not oebakery.call("git checkout --detach refs/tags/%s"%(tag),
                             dir=path):
            err("Failed to checkout submodule %s tag %s"%(
                    path, tag))
            return False
    elif "commit" in params:
        commit = params["commit"]
        if not oebakery.call("git checkout --detach %s"%(commit), dir=path):
            err("Failed to checkout submodule %s commit %s"%(
                    path, commit))
            return False
    elif "branch" in params:
        branch = params["branch"]
        branches = git_branch_status(path)
        if branch in branches:
            if not branches[branch]["current"]:
                if not oebakery.call("git checkout %s"%(branch), dir=path):
                    err("Failed to checkout submodule %s branch %s"%(
                            path, branch))
                    return False
        else:
            if not oebakery.call("git checkout -t -b %s %s"%(
                    branch, "origin/%s"%(branch)), dir=path):
                err("Failed to checkout%s branch %s"%(name, branch))
                return False
        current_remote = oebakery.call(
            "git config --get branch.%s.remote"%(branch),
            dir=path, quiet=True)
        current_merge = oebakery.call(
            "git config --get branch.%s.merge"%(branch),
            dir=path, quiet=True)
        if (current_remote is  None or current_merge is None or
            current_remote.strip() != "origin" or
            current_merge.strip() != "refs/heads/%s"%(branch)):
            if not oebakery.call(
                "git branch --set-upstream %s origin/%s"%(branch, branch),
                dir=path):
                ok = False
    else:
        if not oebakery.call(
            "git submodule update --init --recursive %s"%(path)):
            err("Failed to initialize submodule: %s"%(path))
            ok = False

    return ok


def git_branch_status(path=None, options=None, nobranch=False):
    cmd = "git branch -v --no-abbrev"
    if options:
        cmd += " " + options
    branches = {}
    for line in oebakery.call(cmd, quiet=True, dir=path).split("\n"):
        if not line:
            continue
        asterix = line[0]
        if asterix == "*":
            current = True
        else:
            current = False
        line = line[2:]
        if line[:11] == "(no branch)":
            if not nobranch:
                continue
            name = ""
            line = line[11:]
            line.lstrip()
        else:
            (name, line) = line.split(None, 1)
        commitid, subject = line.split(None, 1)
        branches[name] = {
            "current"	: current,
            "commitid"	:commitid,
            "subject"	: subject,
            }
    return branches


def git_submodule_status(path):
    status = oebakery.call('git submodule status', quiet=True)
    if not status:
        return None
    for line in status.split('\n'):
        if len(line) == 0:
            continue
        if (path == line[1:].split()[1]):
            prefix = line[0]
            commitid = line[1:].split()[0]
            return (prefix, commitid)
    return None


def git_update_remote(name, url, path=None):
    ok = True

    url_split = url.split(",")
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

        return ok

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

    return ok
