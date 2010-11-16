import optparse, sys, os
import oebakery

arguments = "<repository> <directory>"
description = """Clone an OE-lite development environment into a new directory

Arguments:
  repository            OE-lite (git) repository to clone
  directory             directory to to clone into (default is current dir)"""

def run(parser=None, args=None, config=None):

    if parser:
        (options, args) = parser.parse_args(args)
    else:
        (options, args) = args

    if len(args) < 1:
        parser.error('too few arguments')
    if len(args) > 2:
        parser.error('too many arguments')

    if not args:
        parser.error("repository argument required")
    options.repository = args.pop(0)

    if args:
        options.directory = args.pop(0)
    else:
        options.directory = os.path.basename(options.repository)
        if options.directory[-4:] == '.git':
            options.directory = options.directory[:-4]

    if args:
        parser.error("too many arguments")

    if not oebakery.call('git clone %s %s'%(options.repository,
                                            options.directory)):
        return 1

    topdir = oebakery.set_topdir(options.directory)
    oebakery.chdir(options.directory)

    if not oebakery.call('git config push.default tracking'):
        print 'Failed to set push.default = tracking'

    return ("init", ({}, []), config)
