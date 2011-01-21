import oebakery
from oebakery import die, err, warn, info, debug
import oelite.baker

arguments = None
description = """Build stuff"""


def add_parser_options(parser):
    oelite.baker.add_bake_parser_options(parser)
    return


def run(parser, options, args, config):
    baker = oelite.baker.OEliteBaker(options, args, config)

    return baker.bake()
