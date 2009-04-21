#!/usr/bin/env python
from __future__ import with_statement # This isn't required in Python 2.6

import sys, dircache, subprocess, os, string, re, glob, hashlib
from optparse import OptionParser
from ConfigParser import SafeConfigParser
from socket import gethostname


def main():

    usage="""Usage: oe <command> [options]

Allowed oe commands are:
  setup    Setup new OpenEmbedded development environment
  config   Choose local.conf configuration file
  bake     Build recipe
  mirror   Manage download mirror

See 'oe <command> -h' for more information on a specific command."""

    if len(sys.argv) < 2:
        print usage
        return

    if sys.argv[1] == "help":
        if len(sys.argv) == 2:
            print usage
            return
        elif len(sys.argv) == 3:
            sys.argv[1] = sys.argv[2]
            sys.argv[2] = "-h"

    if sys.argv[1] == "setup":
        do_setup(sys.argv[2:])
    elif sys.argv[1] == "config":
        do_config(sys.argv[2:])
    elif sys.argv[1] == "bake" or sys.argv[1] == "bb":
        do_bake(sys.argv[2:])
    elif sys.argv[1] == "mirror":
        do_mirror(sys.argv[2:])
    else:
        print usage
        sys.exit(1)


def do_setup(argv):

    parser = OptionParser("""Usage: oe setup [options]

  Setup OpenEmbedded development environment in the current directory.""")
    parser.add_option("-f", "--file",
                      action="store", type="string", dest="file",
                      help="use configuration file FILE")
    parser.add_option("-b", "--bitbake",
                      action="append_const", dest="what", const="bitbake",
                      help="checkout and configure BitBake")
    parser.add_option("-o", "--openembedded",
                      action="append_const", dest="what", const="openembedded",
                      help="clone and configure OpenEmbedded repository")
    (options, args) = parser.parse_args(argv)

    if options.what == None:
        options.what = ["bitbake", "openembedded"]

    if options.file:
        print "--file not implemented: should download and install file to conf/oe.conf"
        return

    config = read_config()

    if "bitbake" in options.what:

        if not config.has_section("bitbake"):
            print "WARNING: no [bitbake] section in conf/oe.conf"
            config.add_section("bitbake")

        if not config.has_option("bitbake", "url"):
            config.set("bitbake", "url",
                       "http://svn.berlios.de/svnroot/repos/bitbake")
        if not config.has_option("bitbake", "default"):
            config.set("bitbake", "default",
                       "branches/bitbake-1.8")

        do_setup_bitbake(config)

    if "openembedded" in options.what:

        if not config.has_section("openembedded"):
            print "WARNING: no [openembedded] section in conf/oe.conf"
            config.add_section("openembedded")

        if not config.has_option("openembedded", "url"):
            config.set("openembedded", "url",
                       "git://git.openembedded.net/openembedded")
        if not config.has_option("openembedded", "origin_name"):
            config.set("openembedded", "origin_name", "origin")

        do_setup_openembedded(config)

    return


def do_setup_bitbake(config):

    if os.path.exists("bitbake"):
        print "Skipping checkout of bitbake"

    else:
        call(["svn", "co", config.get("bitbake", "url"), "bitbake"])

    with open(".bitbake", "w+") as dot_bitbake:
        dot_bitbake.write("%s\n"%config.get("bitbake", "default"))

    return


def do_setup_openembedded(config):

    if os.path.exists("openembedded"):
        print "Skipping clone of openembedded"

    else:
        if (config.has_option("openembedded", "local_hostname") and
            config.has_option("openembedded", "local_url") and
            gethostname() == config.get("openembedded", "local_hostname")):
            url = config.get("openembedded", "local_url")
        else:
            url = config.get("openembedded", "url")
    
        call(["git", "clone",
              "-o", config.get("openembedded", "origin_name"),
              url, "openembedded"])

    os.chdir("openembedded")
    update = False
    for section in config.sections():
        if (len(section) > len("remote:") and
            section[:len("remote:")] == "remote:"):
            remote = section[len("remote:"):]
            if not config.has_option(section, "url"):
                print >>sys.stderr, "ERROR: no url option in [%s]"%section
                continue
            if os.path.exists(".git/refs/remotes/%s"%(remote)):
                print >>sys.stderr, "Remote %s already created"%remote
                continue
            if call(["git", "remote", "add",
                     remote, config.get(section, "url")]):
                update = True

    if update:
        call(["git", "remote", "update"])

    return


def do_config(argv):

    parser = OptionParser("""Usage: oe config [FILE] [options]

  Configure OpenEmbedded development environment. Choose a local.conf from
  the conf/local.conf.d directory.  If FILE is given, use that. If FILE is
  not given, present user with a menu of available configuration files.""")
    (options, args) = parser.parse_args(argv)

    if len(args) > 1:
        parser.print_help()
        return

    topdir = cd_topdir()

    if len(args) == 0:
        return do_config_menu()

    if len(args) == 1:
        return do_config_file(argv[0])


def do_config_menu():

    if not os.path.isdir("conf/local.conf.d"):
        print >>sys.stderr, "ERROR: conf/local.conf.d directory not found"
        return

    print "Choose configuration file (local.conf will be a symlink to it)\n"
    files = []
    for file in dircache.listdir("conf/local.conf.d"):
        if file[-1:] == '~':
            continue
        files.append(file)
        print " %s: %s"%(("%s"%(len(files))).rjust(3), file)

    answer = raw_input("\nEnter configuration name or number: ")
    try:
        number = int(answer)
        if number > len(files) or number <= 0:
            print >>sys.stderr, "ERROR: invalid number"
            return
        file = files[number-1]
    except:
        if not answer in files:
            print >>sys.stderr, "ERROR: bad configuration name"
            return
        file = answer
        
    return do_config_file(file)


def do_config_file(filename):

    if not os.path.exists("conf/local.conf.d/%s"%filename):
        print >>sys.stderr, "ERROR: %s configuration file not found"%filename
        return

    if (os.path.exists("conf/local.conf") and
        not os.path.islink("conf/local.conf")):
        print >>sys.stderr, "ERROR: conf/local.conf is not a symlink, refusing to remove it"
        return

    if os.path.islink("conf/local.conf"):
        os.remove("conf/local.conf")

    os.symlink("local.conf.d/%s"%filename, "conf/local.conf")

    return


def get_current_topdir(dir):

    if dir == "/":
        return None

    if (os.path.exists("%s/conf/oe.conf"%dir) and
        os.path.exists("%s/openembedded/.git"%dir)):
        return dir

    return get_current_topdir(os.path.dirname(dir))
    

def cd_topdir():
    topdir = get_current_topdir(os.getcwd())
    if not topdir:
        print >>sys.stderr, "ERROR: current directory is not part of an OpenEmbedded development environment"
        sys.exit(1)
    os.chdir(topdir)
    return topdir


def read_config():
    config = SafeConfigParser()

    if not config.read("conf/oe.conf"):
        print >>sys.stderr, "ERROR: failed to parse %s/conf/oe.conf"%os.getcwd()
        sys.exit(1)

 
    return config


def get_simple_config_line(filename, variable):
    if os.path.exists(filename):
        regex = re.compile(variable +'\s*=\s*[\"\'](.*)[\"\']')
        with open(filename) as file:
            for line in file.readlines():
                match = regex.match(line)
                if match:
                    return match.group(1)
    return None


def setup_tmpdir(topdir):
    abi_version = get_simple_config_line("openembedded/conf/abi_version.conf",
                                         "OELAYOUT_ABI")
    if abi_version == None:
        abi_version = 1
    else:
        abi_version = int(abi_version)

    tmpdir = "tmp"
    dottmp = ".tmp"

    if (os.path.exists(tmpdir) and not os.path.islink(tmpdir)):
        return os.path.realpath(tmpdir)

    if (os.path.islink(dottmp) and not os.path.exists(dottmp)):
        print "ERROR: broken .tmp symlink"
        sys.exit(1)

    if os.path.islink(tmpdir):
        os.remove(tmpdir)

    if not os.path.exists(dottmp):
        os.mkdir(dottmp)

    #branch = "hest"
    with open("openembedded/.git/HEAD") as file:
        line = file.readline()
        regex = re.compile('ref: refs/heads/(.*)\n')
        match = regex.match(line)
        if match:
            branch = match.group(1)
        else:
            branch = "__UNKNOWN_BRANCH__"

    abi_tmpdir = os.path.realpath("%s/%s/abi%d"%(dottmp, branch, abi_version))

    if not os.path.exists(abi_tmpdir):
        os.makedirs(abi_tmpdir)

    os.symlink(abi_tmpdir, tmpdir)

    return abi_tmpdir


def version_str_to_tuple(str):
    dash = str.rfind('-')
    if dash >= 0:
        str = str[dash+1:]
    list = string.split(str, '.')
    tuple = ()
    for number in list:
        tuple = tuple + (int(number),)
    return tuple


def do_bake(argv):

    parser = OptionParser("""Usage: oe bake [bitbake options]

  Build recipes using BitBake in the current OpenEmbedded development
  environment.  This can be done from any subdirectory of the OpenEmbedded
  development environment.""")

    topdir = cd_topdir()
    print "OpenEmbedded Bakery",topdir

    config = read_config()

    dot_bitbake_filename = "%s/openembedded/.bitbake"%(topdir)
    bitbake_min_version = None
    if not os.path.exists(dot_bitbake_filename):
        bitbake_min_version = get_simple_config_line(
            "openembedded/conf/sanity.conf",
            "BB_MIN_VERSION")
        dot_bitbake_filename = "%s/.bitbake"%(topdir)
        if not os.path.exists(dot_bitbake_filename):
            print >>sys.stderr, "ERROR: could not determine which BitBake version to use"
            return

    with open(dot_bitbake_filename) as dot_bitbake_file:
        bitbake_version = dot_bitbake_file.readline().rstrip()

    if bitbake_min_version != None:
        if (version_str_to_tuple(bitbake_min_version) >
            version_str_to_tuple(bitbake_version)):
            bitbake_version = "tags/bitbake-%s"%bitbake_min_version
    
    if not os.path.exists("bitbake/%s/bin"%(bitbake_version)):
        print >>sys.stderr, "ERROR: could not find BitBake version %s"%(bitbake_version)

    print "BitBake", bitbake_version

    tmpdir = setup_tmpdir(topdir)
    print "Temp", tmpdir

    os.environ["OE_HOME"] = topdir
    os.environ["OE_TMPDIR"] = tmpdir
    os.environ["BBPATH"] = "%s:%s/openembedded"%(topdir, topdir)
    os.environ["PATH"] = "%s/bitbake/%s/bin:%s"%(topdir, bitbake_version,
                                                 os.environ["PATH"])
    
    if (os.path.exists("%s/openembedded/recipes"%topdir) and
        os.path.exists("%s/openembedded/packages"%topdir)):
        print >>sys.stderr, "ERROR: found both a recipes and packages dir, what to do?"
        return
    elif os.path.exists("%s/openembedded/recipes"%topdir):
        os.environ["OE_BBFILES"] = "%s/openembedded/recipes/*/*.bb"%topdir
    elif os.path.exists("%s/openembedded/packages"%topdir):
        os.environ["OE_BBFILES"] = "%s/openembedded/packages/*/*.bb"%topdir
    else:
        print >>sys.stderr, "ERROR: could not find any BitBake recipes"
        return
    os.environ["BB_ENV_EXTRAWHITE"] = "OE_HOME OE_BBFILES OE_TMPDIR"

    call(["bitbake"] + argv)

    return

    
def do_mirror(argv):
    usage="""Usage oe mirror <sub-command> [options]

Allowed mirror sub-commands are:
  put      Upload local download files to download mirror
  get      Download files from download mirror
  cmp      Compare local download files against download mirror copies
  save     Save list of local download files to download mirror
  load     Load missing files from list of download files on download mirror

See 'oe mirror <sub-command> -h' for more information on a specific sub-command."""

    if len(argv) < 1:
        print usage
        return

    if argv[0] == "help":
        if len(argv) == 1:
            print usage
            return
        elif len(argv) == 2:
            argv[0] = argv[1]
            sys.argv[1] = "-h"

    if argv[0] == "put":
        do_mirror_put(argv[1:])
    elif argv[0] == "get":
        do_mirror_get(argv[1:])
    elif argv[0] == "cmp":
        do_mirror_cmp(argv[1:])
    elif argv[0] == "save":
        do_mirror_save(argv[1:])
    elif argv[0] == "load":
        do_mirror_load(argv[1:])
    else:
        print usage
        sys.exit(1)


def do_mirror_put(argv):

    parser = OptionParser("""Usage: oe mirror put [file]*

  Upload file(s) from downloads directory to download mirror.""")
    parser.add_option("-c", "--check-md5",
                      action="store_true", dest="check_md5", default=False,
                      help="verify MD5 sums")
    parser.add_option("-i", "--interactive",
                      action="store_true", dest="interactive", default=False,
                      help="interactive mode")
    (options, args) = parser.parse_args(argv)

    if len(args) == 0:
        args = ['*']

    topdir = cd_topdir()
    print "OpenEmbedded Bakery",topdir

    config = read_config()

    if not config.has_section("mirror"):
        print >>sys.stderr, "ERROR: no [mirror] section in conf/oe.conf"
        return
    if not config.has_option("mirror", "put_hostname"):
        print >>sys.stderr, "ERROR: no put_hostname option in conf/oe.conf"
        return
    if not config.has_option("mirror", "put_path"):
        print >>sys.stderr, "ERROR: no put_path option in conf/oe.conf"
        return

    os.chdir('downloads')

    local_files = ls_local_files(args)

    local_files = filter_local_files_missing_md5(
        local_files, options.interactive)

    if options.check_md5:
        filter_bad_md5_files(local_files, options.interactive)

    if len(local_files) == 0:
        print "No files to upload"
        return

    mirror_files = ls_mirror_files(config)

    mirror_files = filter_mirror_files_in_local_files(mirror_files, local_files)

    (mirror_files, local_files) = filter_mirror_files_md5_sanity(
        mirror_files, local_files, options.interactive)

    if options.check_md5:
        filter_compare_md5(local_files, mirror_files, config,
                           options.interactive)
    else:
        local_files = filter_local_files_not_in_mirror_files(
            local_files, mirror_files)

    if len(local_files) == 0:
        print "No files to upload"
        return

    md5_files = []
    for file in local_files:
        md5_files += [file + '.md5']
    local_files = local_files + md5_files
    local_files.sort()

    call(['scp'] + local_files +
         [config.get('mirror', 'put_hostname') + ':' +
          config.get('mirror', 'put_path')])

    return



def ls_mirror_files(config):
    pipe = subprocess.Popen(
        ['ssh', config.get('mirror', 'put_hostname'),
         'ls', config.get('mirror', 'put_path')],
        stdout=subprocess.PIPE)
    
    mirror_files = []
    for file in pipe.stdout.readlines():
        file = file.rstrip()
        mirror_files.append(file)

    return mirror_files


def filter_mirror_files_in_local_files(mirror_files, local_files):
    filtered_mirror_files = []
    for file in mirror_files:
        if file[-4:] == '.md5':
            if file[:-4] in local_files:
                filtered_mirror_files.append(file)
        else:
            if file in local_files:
                filtered_mirror_files.append(file)
    return filtered_mirror_files


def filter_mirror_files_md5_sanity(mirror_files, local_files, interactive):

    filtered_mirror_files = []
    for file in mirror_files:
        if file[-4:] == '.md5':
            if not file[:-4] in mirror_files:
                print '\nWARNING: mirror has orphan MD5 sum for', file
            else:
                filtered_mirror_files.append(file)
        else:
            filtered_mirror_files.append(file)

    filtered_local_files = []
    for file in local_files:
        if (file in mirror_files) and (not file + '.md5' in mirror_files):
            print '\nWARNING: mirror missing MD5 sum for', file
            if interactive:
                while True:
                    answer = raw_input(
                        "(s)kip file, (o)verwrite mirror copy: ")
                    if answer == 's':
                        break
                    elif answer == 'o':
                        filtered_local_files.append(file)
                        break
                    else:
                        continue
        else:
            filtered_local_files.append(file)

    return (filtered_mirror_files, filtered_local_files)


def filter_compare_md5(local_files, mirror_files, config, interactive):

    i = 0
    for file in local_files:
        md5_file = file + '.md5'
        if md5_file in mirror_files:
            mirror_md5 = subprocess.Popen(
                ['ssh', config.get('mirror', 'put_hostname'),
                 'cat',
                 os.path.join(config.get('mirror', 'put_path'), md5_file)],
                stdout=subprocess.PIPE).communicate()[0]
            with open(md5_file, "r") as local_md5_file:
                local_md5 = local_md5_file.readline()
            if local_md5 != mirror_md5:
                print "\nWARNING: local %s differs from mirror copy"%file
                print 'local  =', local_md5
                print 'mirror =', mirror_md5
                if interactive:
                    while True:
                        answer = raw_input(
                            "(s)kip file, (o)verwrite mirror copy, (g)et mirror copy: ")
                        if answer == 's':
                            del local_files[i]
                            break
                        elif answer == 'o':
                            break
                        elif answer == 'g':
                            print "WARNING: get not implemented"
                            del local_files[i]
                            break
                        else:
                            continue
            else:
                del local_files[i]
                break
        i += 1


def ls_local_files(args):
    local_files = []

    for arg in args:

        files = glob.glob(arg)
        files.sort()

        for file in files:

            if not os.path.isfile(file):
                continue
            if file[-4:] == '.md5':
                continue
            if file[-5:] == '.lock':
                continue
            if file[:4] == 'git_':
                continue
            if file[:4] == 'cvs_':
                continue
            if file[:4] == 'svn_':
                continue

            local_files.append(file)

    return local_files


def filter_local_files_missing_md5(local_files, interactive):
    filtered_local_files = []
    for file in local_files:
        md5_file = file + '.md5'
        if not os.path.exists(md5_file):
            print "\nWARNING: no MD5 sum for", file
            if interactive:
                while True:
                    answer = raw_input(
                        "(s)kip file, (r)emove file, (g)enerate md5: ")
                    if answer == 's':
                        break
                    elif answer == 'r':
                        os.remove(file)
                        break
                    elif answer == 'g':
                        with open(md5_file, "w+") as wfile:
                            wfile.write(calc_md5sum(file))
                        filtered_local_files.append(file)
                        break
                    else:
                        continue

        else:
            filtered_local_files.append(file)
            
    return filtered_local_files


def filter_bad_local_md5(local_files, interactive):

    for file in local_files:
        md5_filename = file + '.md5'
        with open(md5_file, "r") as local_md5_file:
            local_md5 = local_md5_file.readline()
        local_md5_gen = calc_md5sum(file)
        if local_md5_gen != local_md5:
            print "\nWARNING: bad MD5 sum for", file
            if interactive:
                while True:
                    answer = raw_input(
                        "(s)kip file, (r)emove file, (g)enerate new md5 file: ")
                    if answer == 's':
                        del local_files[i]
                        break
                    elif answer == 'r':
                        os.remove(file)
                        del local_files[i]
                        break
                    elif answer == 'g':
                        with open(file+'.md5', "w+") as wfile:
                            wfile.write(local_md5_gen)
                        break
                    else:
                        continue
            else:
                del local_files[i]

    return


def filter_local_files_not_in_mirror_files(local_files, mirror_files):

    filtered_local_files = []
    for file in local_files:
        if not file in mirror_files:
            filtered_local_files.append(file)
    return filtered_local_files

def calc_md5sum(filename):
    m = hashlib.md5()
    with open(filename, "r") as file:
        while True:
            bytes = file.read(4096)
            if len(bytes) == 0:
                break
            m.update(bytes)
    return m.hexdigest()

    
def call(cmd):
    print "\n>",
    for c in cmd:
        print c,
    print

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError, e:
        print >>sys.stderr, "Execution failed:", e
        return False

    return True


if __name__ == "__main__":
    main()
