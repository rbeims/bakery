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
    
    baker = oelite.baker.OEliteBaker(config)

    if baker.bake(options, args):
        return 0
    else:
        return 1
