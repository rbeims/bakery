import optparse, sys, os
import oebakery


description = "Clone an OE-lite repository into a new directory"
arguments = (
    ("repository", "OE-lite repository to clone from", 0),
    ("directory", "directory to clone into (default is repository name)", 1))
flags = ("no-bakery-conf")


def parse_args(options, args):
    if not args:
        return "repository argument required"
    if len(args) < 1:
        return "too few arguments"
    if len(args) > 2:
        return "too many arguments"
    options.repository = args.pop(0)
    if args:
        options.directory = args.pop(0)
    else:
        options.directory = options.repository.strip("/")
        options.directory = os.path.basename(options.directory)
        if options.directory[-4:] == '.git':
            options.directory = options.directory[:-4]
    return 0


def run(options, args, config):
    if not oebakery.call('git clone --recursive %s %s'%(
            options.repository, options.directory)):
        return "git clone failed"

    topdir = oebakery.set_topdir(options.directory)
    oebakery.chdir(options.directory)

    oebakery.path.copy_local_conf_sample("conf")

    if not oebakery.call('git config push.default tracking'):
        print 'Failed to set push.default = tracking'

    return ["update"]
