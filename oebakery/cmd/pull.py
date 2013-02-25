import os

import oebakery
logger = oebakery.logger
import update


# oe pull
# pull oe-lite.git repo and all submodules, branch submodules are git
# pull'ed, non-branch submodules are git submodule add'ed.

# oe pull . meta/core meta/base
# pull oe-lite.git repo and submodules meta/core and meta/base.

# oe pull meta/core
# pull submodule meta/core.


args = "[<path>...]"
description = ("Fetch changes from upstream repositories", """
  When called without path arguments, fetch and merge head of main repository,
  checkout the submodule versions stored in main repository for all non-branch
  submodules, and fetch and merge head of branch submodules.

  When called with a list of submodule paths, pull only those modules.
  Use "." to specify main repository.""")


def add_parser_options(parser):
    parser.add_option("-r", "--remotes",
                      action="store_true", dest="remotes", default=False,
                      help="fetch updates for remote tracking branches")
    return


def run(options, args, config):
    if not args or "." in args:
        options.main = True
    else:
        options.main = False
    paths = []
    submodules = []
    for path, url, params in config["__submodules"]:
        if not args or path in args:
            paths.append(path)
            submodules.append((path, url, params))

    if not os.path.exists(".git"):
        return "Aiee!  This is not even a git repository: %s"%(os.getcwd())

    if options.main:
        if options.remotes and not git_remote_update():
            return 1
        if not git_pull():
            return 1

    if options.remotes:
        for path in paths:
            git_remote_update(path)

    # get list of submodules
    #current = {}
    #for line in oebakery.call("git submodule status", quiet=True)\
    #        .split("\n"):
    #    if len(line) == 0:
    #        continue
    #
    #    path = line[1:].split()[1]
    #    prefix = line[0]
    #    commitid = line[1:].split()[0]
    #
    #    fetch_url = None
    #    push_url = None
    #    branch = None
    #    remotes = None
    #
    #    current[path] = (prefix, commitid)

    ok = True
    for path, url, params in submodules:
        if not update.update_submodules([(path, url, params)]):
            ok = False
            continue
        if "branch" in params:
            if not git_pull(path, params["branch"]):
                ok = False

    return not ok


def git_pull(path=None, branch=None):
    if path:
        name = " submodule %s"%(path)
    else:
        name = ""
    if not oebakery.call("git pull", dir=path):
        logger.error("Failed to pull %s"%(name))
        return False
    return True


def git_remote_update(path=None):
    # older git versions return 1 on success, and newer versions 0
    # so we will just ignore the return code for now
    oebakery.call("git remote update", dir=path)
    remotes = oebakery.call("git remote", dir=path, quiet=True)
    ok = True
    if remotes:
        for remote in remotes.split("\n"):
            if not remote or len(remote) == 0:
                continue
            if not oebakery.call("git remote prune %s"%(remote),
                                 dir=path):
                msg = "Failed to prune remote %s"%(remote)
                if path:
                    msg += " in %s"%(path)
                logger.error(msg)
                ok = False
    return ok
