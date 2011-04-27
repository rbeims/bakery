import oebakery
from oebakery import die, err, warn, info, debug
import oelite.baker

arguments = None
description = """Build stuff"""


def add_parser_options(parser):
    oelite.baker.add_bake_parser_options(parser)
    return


def run(parser, options, args, config):
    try:
        baker = oelite.baker.OEliteBaker(options, args, config)
    except oelite.parse.ParseError, e:
        print "ERROR:",
        e.print_details()
        print "Aborting"
        return 1

    return baker.bake()
