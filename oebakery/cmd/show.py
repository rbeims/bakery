import oebakery
import oelite.baker


description = "Show metadata"


def add_parser_options(parser):
    oelite.baker.add_show_parser_options(parser)
    parser.add_option("-d", "--debug",
                      action="store_true",
                      help="Debug the OE-lite metadata")
    return


def run(options, args, config):
    oebakery.log.configure_legacy_logging(options.debug)
    baker = oelite.baker.OEliteBaker(options, args, config)
    return baker.show()
