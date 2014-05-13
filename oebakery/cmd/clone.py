import optparse
import sys
import os

import oebakery
logger = oebakery.logger
import oebakery.gitmodules


description = "Clone an OE-lite repository into a new directory"
arguments = (
    ("repository", "OE-lite repository to clone from", 0),
    ("directory", "directory to clone into (default is repository name)", 1))
flags = ("no-bakery-conf")


def add_parser_options(parser):
    parser.add_option("--bare",
                      action="store_true", default=False,
                      help="Create a bare OE-lite repository")
    parser.add_option("--mirror",
                      action="store_true", default=False,
                      help="Create a mirror OE-lite repository")
    parser.add_option("-b", "--branch", action='store', type=str,
                      help="repository branch to checkout initially"
                      " [default: %(default)s]")
    return


def parse_args(options, args):
    if not args:
        return "repository argument required"
    if len(args) < 1:
        return "too few arguments"
    if len(args) > 2:
        return "too many arguments"
    if options.mirror:
        options.bare = True
    options.repository = args.pop(0)
    if args:
        options.directory = args.pop(0)
    else:
        options.directory = options.repository.strip("/")
        options.directory = os.path.basename(options.directory)
        if not options.bare and options.directory[-4:] == '.git':
            options.directory = options.directory[:-4]
        elif options.bare and options.directory[-4:] != '.git':
            options.directory = options.directory + '.git'
    return 0


def run(options, args, config):
    if options.bare:
        return clone_bare(options)
    else:
        return clone_checkout(options)


def clone_checkout(options):
    if options.branch:
        branch_arg = ' --branch %s'%(options.branch)
    else:
        branch_arg = ''
    if not oebakery.call('git clone --recursive %s%s %s'%(
            options.repository, branch_arg ,options.directory)):
        return "git clone failed"

    topdir = oebakery.set_topdir(options.directory)
    oebakery.chdir(options.directory)

    oebakery.path.copy_local_conf_sample("conf")

    if not oebakery.call('git config push.default tracking'):
        print 'Failed to set push.default = tracking'

    return ["update"]


def clone_bare(options):
    global clone_cmd
    clone_cmd = 'git clone %s %%s %%s'%(
        ['--bare', '--mirror'][int(options.mirror)])
    failed = clone_bare_recursive(options.repository, options.directory)
    if failed:
        return "failed repositories: %s"%(', '.join(failed))

def clone_bare_recursive(repository, directory):
    if not oebakery.call(clone_cmd%(repository, directory)):
        logger.error("bare clone of module %s failed", directory)
        return [directory]
    gitmodules = oebakery.call(
        "git cat-file blob HEAD:.gitmodules", dir=directory, quiet=True)
    if not gitmodules:
        return
    submodules = oebakery.gitmodules.parse_dot_gitmodules(buffer=gitmodules)
    failed = []
    for submodule in submodules.values():
        path = submodule['path']
        url = submodule['url']
        if url != './' + path: # only clone relative submodules
            continue
        ret = clone_bare_recursive(
            os.path.join(repository, path), os.path.join(directory, path))
        if ret:
            failed.extend(ret)
    return failed
