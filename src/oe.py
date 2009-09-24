#!/usr/bin/env python
from __future__ import with_statement # This isn't required in Python 2.6
import sys, dircache, subprocess, os, string, re, glob, hashlib

def main():

    usage="""Usage: oe <command> [options]*

Allowed oe commands are:
  init        Setup new OE Bakery development environment
  update      Update OE Bakery development environment
  config      Choose configuration file
  bake        Build recipe
  ingredient  Manage ingredient (downloaded sources) files
  prebake     Manage prebake (packaged staging) files

See 'oe <command> -h' or 'oe help <command> for more information on a
specific command."""

    if len(sys.argv) < 2:
        print usage
        return

    if sys.argv[1] == "help":
        if len(sys.argv) == 3:
            sys.argv[1] = sys.argv[2]
            sys.argv[2] = "-h"
        else:
            print usage
            return

    sys.path.insert(0,os.path.join(
            os.path.dirname(os.path.realpath(sys.argv[0])), 'lib'))
    import bakery
    from bakery.cmd_init import InitCommand
    from bakery.cmd_update import UpdateCommand
    from bakery.cmd_bake import BakeCommand
    #from bakery.cmd_ingredient import IngredientCommand
    #from bakery.cmd_prebake import PrebakeCommand
    from bakery import misc

    if sys.argv[1] == "init":
        cmd = InitCommand(sys.argv[2:])
        return cmd.run()

    topdir = bakery.get_topdir()
    os.chdir(topdir)

    config = bakery.read_config()

    if sys.argv[1] == "update":
        cmd = UpdateCommand(config, sys.argv[2:])

    elif sys.argv[1] == "bake":
        cmd = BakeCommand(config, sys.argv[2:])

    elif sys.argv[1] == "ingredient":
        cmd = IngredientCommand(config, sys.argv[2:])

    elif sys.argv[1] == "prebake":
        cmd = PrebakeCommand(config, sys.argv[2:])

    else:
        print usage
        sys.exit(1)

    return cmd.run()
    

if __name__ == "__main__":
    main()
