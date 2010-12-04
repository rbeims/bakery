#!/usr/bin/env python
import sys, os, optparse
import dircache, subprocess, string, re, glob, hashlib

VERSION = "%prog 0.1foobar"

def main():

    usage="""Usage: oe <command> [options]*

Allowed oe commands are:
  init        Setup new OE Bakery development environment
  clone       Clone an OE Bakery development environment into a new directory
  update      Update OE Bakery development environment accoring to configuration
  pull        Pull updates from remote repositories
  tmp         Manage TMPDIR directories
  bake        Build recipe (call bitbake)

See 'oe <command> -h' or 'oe help <command> for more information on a
specific command."""
    # FIXME: generate the list of allowed commands dynamically based
    # on available oebakery.cmd_* modules

    parser = optparse.OptionParser(
        """Usage: %prog [OPTIONS] <COMMAND>""",
        version=VERSION)

    parser.add_option("-v", "--verbose",
                      action="store_true",
                      help="make noise")

    parser.add_option("-q", "--quiet",
                      action="store_true",
                      help="don't make so much noise")

    parser.add_option("-d", "--debug",
                      action="store_true",
                      help="make a lot of noise")

    parser.add_option("-Q", "--really-quiet",
                      action="store_true",
                      help="Sshhh!")

    # HACK to force running from source directory
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

    try:
        import oebakery
    except ImportError, e:
        # hack to be able to run from source directory
        sys.path.insert(
            0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        try:
            import oebakery
        except ImportError, e:
            print >>sys.stderr, "ERROR: Cannot find OE-lite Bakery module"
            sys.exit(err)

    from oebakery import die, err, warn, info, debug

    # Supported commands
    cmds = ("clone", "init", "update", "pull", "bake", "show", "tmp")

    # Look for a valid COMMAND
    def find_cmd(args, cmds):
        index = next((i for i in xrange(len(args))
                      if args[i] in cmds), None)
        return index
    cmd_index = find_cmd(sys.argv[1:], ("help",) + cmds)

    # Support "help" argument as alias for -h/--help option
    if cmd_index is not None and sys.argv[1 + cmd_index] == "help":
        sys.argv[1 + cmd_index] = "-h"
        cmd_index = find_cmd(sys.argv[1:], cmds)

    # Add list of commands to usage
    if cmd_index is None:
        usage = parser.get_usage()
        usage += "\nCommands:"
        for cmd in cmds:
            usage += "\n  %-21s "%(cmd)
            # FIXME: dynamically add usage description from cmd_*.DESCRIPTION
            usage += "TBD"
        parser.set_usage(usage)
        (options, args) = parser.parse_args()
        parser.error("You must specify a valid COMMAND argument")

    def cmd_usage(parser, cmd_name, cmd):
        try:
            description = cmd.description
        except AttributeError, e:
            description = ""
        try:
            if cmd.arguments:
                arguments = " " + cmd.arguments
            else:
                arguments = ""
        except AttributeError, e:
            arguments = ""
        parser.set_usage(
            """Usage: %%prog [OPTIONS] %s%s

  %s."""%(cmd_name, arguments, description))

    # Setup first command to run
    cmd_args = sys.argv[1:]
    cmd_name = cmd_args[cmd_index]
    del cmd_args[cmd_index]
    topdir = None
    config = None

    while cmd_name:

        if cmd_name != "clone":

            if topdir is None:
                topdir = oebakery.locate_topdir()
            oebakery.chdir(topdir)

            if config is None:

                sys.path.insert(0, os.path.abspath("bitbake/lib"))
                import bb.parse, bb.data
                bb.msg.set_debug_level(0)

                if cmd_name != "init":
                    if not "__oe_lite__" in dir(bb):
                        die("BitBake is not OE-lite Bitbake!")

                # in case of clone/init, there might not be a
                # topdir/bitbake/lib and we rely on bitbake being
                # provided from host, and accept a normal BitBake
                # version.

                config = bb.parse.handle(os.path.abspath("conf/oe-lite.conf"),
                                         bb.data.init())
                config_defaults(config)
                config.setVar("TOPDIR", topdir)

        # Import the chosen command
        cmd = __import__("oebakery.cmd_" + cmd_name,
                         globals(), locals(),
                         ["run", "description", "arguments"], -1)

        # Adjust usage
        if parser:
            cmd_usage(parser, cmd_name, cmd)

        if "add_parser_options" in dir(cmd):
            cmd.add_parser_options(parser)

        if parser:
            (options, cmd_args) = parser.parse_args(cmd_args)
        else:
            (options, cmd_args) = cmd_args

        if options:
            oebakery.DEBUG = options.debug

        exitcode = cmd.run(parser, options, cmd_args, config)

        if isinstance(exitcode, int):
            break

        (cmd_name, cmd_args, config) = exitcode
        parser = None
        continue

    return exitcode


def config_defaults(config):
    ok = True

    from oebakery import die, err, warn, info, debug

    BBPATH = (config.getVar('BBPATH', 0) or ".").split(":")

    if not BBPATH:
        BBPATH = ["."]
        OE_MODULES = config.getVar("OE_MODULES")
        for submodule in OE_MODULES.split():
            module_path = config.getVar("OE_MODULE_PATH_" + submodule, 0)
            if not module_path:
                path = "meta/" + submodule
            BBPATH.append(path)

    config.setVar("BBPATH", ":".join(map(os.path.abspath, BBPATH)))
    config.setVar("BBPATH_PRETTY", ":".join(BBPATH))

    BBRECIPES = config.getVar('BBRECIPES', 0) or []
    if BBRECIPES:
        BBRECIPES = BBRECIPES.split(":")

    if not BBRECIPES:
        for i in range(len(BBPATH)):
            bbrecipes = os.path.join(BBPATH[i], "recipes")
            if os.path.isdir(bbrecipes):
                BBRECIPES.append(os.path.join(bbrecipes, "*/*.bb"))

    config.setVar("BBFILES", " ".join(map(os.path.abspath, BBRECIPES)))
    config.setVar("BBFILES_PRETTY", " ".join(BBRECIPES))

    for bbpath in BBPATH:
        bblib = os.path.abspath(os.path.join(bbpath, "lib"))
        if os.path.isdir(bblib):
            sys.path.insert(0, bblib)

    #debug("BBPATH = %s"%(config.getVar("BBPATH", 0)))
    #debug("BBFILES = %s"%(config.getVar("BBFILES", 0)))
    #debug("PYTHONPATH = %s"%sys.path)
    
    return
    

if __name__ == "__main__":
    exitcode = main()
    sys.exit(exitcode)
