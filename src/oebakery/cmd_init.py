import optparse, sys, os
import subprocess, socket, shutil
import oebakery
from oebakery import die, err

arguments = None
description = """Setup OE-lite environment in the current directory"""

def run(parser, args, config=None):

    if parser:
        (options, args) = parser.parse_args(args)
    else:
        (options, args) = args

    topdir = oebakery.set_topdir(os.path.curdir)

    if not os.path.exists(".git"):

        if not oebakery.call("git init"):
            die("Failed to initialize git")
            return

        if not oebakery.call("git config push.default tracking"):
            die("Failed to set push.default = tracking")

    oebakery.copy_local_conf_sample(config.getVar("CONFDIR", 0) or "conf")

    return ("update", ({}, []), config)
