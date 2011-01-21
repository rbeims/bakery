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
    baker = oelite.baker.OEliteBaker(options, args, config)

    return baker.show()
