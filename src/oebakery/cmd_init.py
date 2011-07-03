import optparse, sys, os
import subprocess, socket, shutil
import oebakery
from oebakery import die, err

arguments = None
description = """Setup OE-lite environment in the current directory"""

def run(parser, options, args, config=None):

    topdir = oebakery.set_topdir(os.path.curdir)

    if not os.path.exists(".git"):

        if not oebakery.call("git init"):
            die("Failed to initialize git")

        if not oebakery.call("git config push.default tracking"):
            die("Failed to set push.default = tracking")

    oebakery.copy_local_conf_sample(config["CONFDIR"] or "conf")

    return ("update", ({}, []), config)
