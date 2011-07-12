import oebakery
from oebakery import die, err, warn, info, debug, FatalError
import oelite.baker

arguments = None
description = """Build stuff"""


def add_parser_options(parser):
    oelite.baker.add_bake_parser_options(parser)
    return


def run(parser, options, args, config):
    try:
        baker = oelite.baker.OEliteBaker(options, args, config)
        return baker.bake()
    except FatalError:
        return 1
    except Exception, e:
        import traceback
        import sys
        if "print_details" in dir(e):
            print "\nERROR:", e
            e.print_details()
            if options.debug:
                traceback.print_exc()
        else:
            print "ERROR: Uncaught Python exception"
            traceback.print_exc()
        print "ERROR: initializing baker failed, aborting!"
        return 1
