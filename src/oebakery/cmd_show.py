import oebakery
from oebakery import die, err, warn, info, debug
import oelite.baker

arguments = None
description = """Show stuff"""


def add_parser_options(parser):
    oelite.baker.add_show_parser_options(parser)
    return


def run(parser, options, args, config):
    options.quiet = True

    def fail():
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

    try:
        baker = oelite.baker.OEliteBaker(options, args, config)
    except FatalError:
        return 1
    except Exception, e:
        fail()
        print "ERROR: initializing baker failed, aborting!"
        return 1

    try:
        return baker.show()
    except FatalError:
        return 1
    except Exception, e:
        fail()
        print "ERROR: baker show failed, aborting!"
        return 1
