#!/usr/bin/env python
import sys, dircache, subprocess, os, string, re, glob, hashlib

def main():

    usage="""Usage: oe <command> [options]*

Allowed oe commands are:
  init        Setup new OE Bakery development environment
  clone       Clone an OE Bakery development environment into a new directory
  update      Update OE Bakery development environment
  tmp         Manage TMPDIR directories
  bake        Build recipe (call bitbake)
  ingredient  Manage ingredient (downloaded sources) files
  prebake     Manage prebake (packaged staging) files

See 'oe <command> -h' or 'oe help <command> for more information on a
specific command."""

    if len(sys.argv) < 2 or (len(sys.argv) == 2 and sys.argv[1] == '-h'):
        print usage
        return

    if sys.argv[1] == "help":
        if len(sys.argv) == 3:
            sys.argv[1] = sys.argv[2]
            sys.argv[2] = "-h"
        else:
            print usage
            return

    # hack to be able to run from source directory
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

    import oebakery
    from oebakery.cmd_init import InitCommand
    from oebakery.cmd_clone import CloneCommand
    from oebakery.cmd_update import UpdateCommand
    from oebakery.cmd_tmp import TmpCommand
    from oebakery.cmd_bake import BakeCommand
    #from oebakery.cmd_ingredient import IngredientCommand
    #from oebakery.cmd_prebake import PrebakeCommand
    from oebakery import misc

    if sys.argv[1] == "init":
        cmd = InitCommand(sys.argv[2:])
        return cmd.run()

    elif sys.argv[1] == "clone":
        cmd = CloneCommand(sys.argv[2:])
        return cmd.run()

    topdir = oebakery.locate_topdir()
    if topdir != os.environ['PWD']:
        oebakery.chdir(topdir)

    config = oebakery.read_config()

    if sys.argv[1] == "update":
        cmd = UpdateCommand(config, sys.argv[2:])

    elif sys.argv[1] == "tmp":
        cmd = TmpCommand(config, sys.argv[2:])

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
