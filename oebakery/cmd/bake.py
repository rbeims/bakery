import oebakery
import oelite.baker


description = "Build something"


def add_parser_options(parser):
    oelite.baker.add_bake_parser_options(parser)
    parser.add_option("-d", "--debug",
                      action="store_true", default=False,
                      help="Debug the OE-lite metadata")
    return


def run(options, args, config):
    oebakery.log.configure_legacy_logging(options.debug)
    baker = oelite.baker.OEliteBaker(options, args, config)
    return baker.bake()
