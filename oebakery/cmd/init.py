import os

import oebakery


description = "Create new OE-lite manifest repository"
arguments = None
flags = ("no-oestack")


# To be run from a directory that is _not_ a git repository yet.

def run(options, args, config):
    topdir = oebakery.set_topdir(os.path.curdir)

    if oebakery.call("git status", quiet=True):
        oebakery.fatal("Already initialized: %s"%(topdir))

    if not oebakery.call("git init"):
        oebakery.fatal("Failed to initialize git")

    if not oebakery.call("git config push.default tracking"):
        oebakery.fatal("Failed to set push.default = tracking")

    oebakery.path.copy_local_conf_sample(config["CONFDIR"] or "conf")

    return ["update"]
