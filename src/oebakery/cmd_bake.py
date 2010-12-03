import oebakery
from oebakery import die, err, warn, info, debug
import oelite.baker

arguments = None
description = """Build stuff"""

def run(parser, args, config):
    ok = True

    oelite.baker.add_parser_options(parser)

    if parser:
        (options, args) = parser.parse_args(args)
    else:
        (options, args) = args

    oebakery.DEBUG = options.debug

    baker = oelite.baker.OEliteBaker(options, args, config)

    if baker.bake():
        return 0
    else:
        return 1
