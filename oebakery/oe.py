#!/usr/bin/env python

VERSION = "4.0.3"

# New arguments strategy: oe [bakery options] <command> [command options]
#
# the bakery options should only apply to the bakery tool itself, and not the
# command as such (even if a builtin command).  Only bakery options supported
# are "-d|--debug" for bakery tool debugging, "-v|--version" for bakery tool
# version information, "-h|--help" for general bakery tool usage information.

import sys
import os
import optparse
import logging

# Force stdout and stderr into un-buffered mode.  This seems to unbreak the
# FUBAR stdout/stderr handling in Jenkins for now...
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 0)

# Parse bakery command-line options
parser = optparse.OptionParser(
    """
  %prog [--version] [-h|--help] [-d|--debug] <command> [options] [<args>]""",
    version="OE-lite Bakery %s"%(VERSION))
parser.add_option("-d", "--debug",
                  action="store_true",
                  help="Debug the OE-lite Bakery tool itself")
parser.disable_interspersed_args()
bakery_options, cmd_argv = parser.parse_args(sys.argv[1:])

def module_version(module):
    try:
        return module.__version__
    except AttributeError:
        return "unknown"

# Import oebakery modules
try:
    import oebakery
    if module_version(oebakery) != VERSION:
        del sys.modules["oebakery"]
        del oebakery
        raise Exception()
except:
    if bakery_options.debug:
        print "DEBUG: bakery: importing oebakery module from source directory:", os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    try:
        import oebakery
        version = module_version(oebakery)
        if version != VERSION:
            print >>sys.stderr, "CRITICAL: bad oebakery module version: %s (expected: %s)"%(version, VERSION)
            sys.exit(1)
    except ImportError, e:
        print >>sys.stderr, "CRITICAL: cannot import oebakery module"
        print e
        sys.exit(1)

# Initialize logging
logger = oebakery.logger
if bakery_options.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

logger.debug("OE-lite Bakery %s", oebakery.__version__)
logger.debug("bakery_options = %s", bakery_options)
logger.debug("cmd_argv = %r", cmd_argv)

# Show list of available commands
if not cmd_argv or (len(cmd_argv) == 1 and cmd_argv[0] == "help"):
    config = oebakery.parse.parse_bakery_conf()
    oebakery.cmd.add_builtin_cmds()
    oebakery.cmd.add_manifest_cmds()
    usage = parser.get_usage() + "\n" + oebakery.cmd.cmds_usage()
    print usage
    sys.exit(1)

if cmd_argv[0] == "help":
    cmd_argv = cmd_argv[1:] + ["-h"]

config = None

while cmd_argv:
    logger.debug(" ".join(cmd_argv))
    cmd_name = cmd_argv.pop(0)
    oebakery.cmd.clear()
    oebakery.cmd.add_builtin_cmds()
    cmd = oebakery.cmd.get_cmd(cmd_name)

    if config is None and (cmd is None or not "no-bakery-conf" in cmd.flags):
        config = oebakery.parse.parse_bakery_conf()

    if cmd is None:
        oebakery.cmd.add_manifest_cmds()
        cmd = oebakery.cmd.get_cmd(cmd_name)

    if cmd is None:
        logger.critical("Invalid command: %s", cmd_name)
        logger.info("Use '%s help' to get list of available commands.",
                     os.path.basename(sys.argv[0]))
        sys.exit(1)

    parser = oebakery.cmd.cmd_parser(cmd)
    if parser is None:
        logger.critical("%s failed", cmd.name)
        sys.exit(1)
    cmd_options, cmd_args = parser.parse_args(cmd_argv)

    ret = oebakery.cmd.call(cmd, "parse_args", cmd_options, cmd_args)
    if ret:
        logger.critical("%s failed: %s", cmd.name, ret)
        sys.exit(1)

    ret = oebakery.cmd.call(cmd, "run", cmd_options, cmd_args, config)
    if isinstance(ret, list):
        cmd_argv = ret
        continue
    elif ret:
        logger.critical("%s failed: %s", cmd.name, ret)
        sys.exit(1)
    else:
        cmd_argv = []

logger.debug("all done")
sys.exit(0)
