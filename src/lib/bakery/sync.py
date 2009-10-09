from __future__ import with_statement # This isn't required in Python 2.6

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
    parser.add_option("-n", "--dry-run",
                      action="store_true", dest="dry_run", default=False,
                      help="perform a trial run with no changes made")
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

    local_files = ls_local_files(args, options)

    if len(local_files) == 0:
        print "No files to upload"
        return

    local_files = mirror_files_filter(config, options, local_files)

    if len(local_files) == 0:
        print "No files to upload"
        return

    md5_files = []
    for file in local_files:
        md5_files += [file + '.md5']
    local_files = local_files + md5_files
    local_files.sort()

    local_files_str = ""
    for file in local_files:
        local_files_str = local_files_str + ' ' + file

    call("scp%s %s:%s"%(local_files_str,
                         config.get('mirror', 'put_hostname'),
                         config.get('mirror', 'put_path')),
         dry_run=options.dry_run)

    return


def ls_local_files(args, options):
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

    filtered_local_files = []
    for file in local_files:
        md5_file = file + '.md5'
        if not os.path.exists(md5_file):
            print "\nWARNING: no MD5 sum for", file
            if options.interactive:
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
            
    local_files = filtered_local_files

    if options.check_md5:
        filtered_local_files = []
        for file in local_files:
            md5_filename = file + '.md5'
            with open(md5_file, "r") as local_md5_file:
                local_md5 = local_md5_file.readline()
            local_md5_gen = calc_md5sum(file)
            if local_md5_gen == local_md5:
                filtered_local_files.append(file)
            else:
                print "\nWARNING: bad MD5 sum for", file
                if options.interactive:
                    while True:
                        answer = raw_input(
                            "(s)kip file, (r)emove file, (g)enerate new md5 file: ")
                        if answer == 's':
                            break
                        elif answer == 'r':
                            os.remove(file)
                            break
                        elif answer == 'g':
                            with open(file+'.md5', "w+") as wfile:
                                wfile.write(local_md5_gen)
                                filtered_local_files.append(file)
                            break
                        else:
                            continue
                else:
                    continue
        local_files = filtered_local_files

    return local_files



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


def mirror_files_filter(config, options, local_files):

    mirror_files = ls_mirror_files(config)

    mirror_files = remove_not_in_local_files(mirror_files, local_files)

    (mirror_files, local_files) = filter_mirror_files_md5_sanity(
        mirror_files, local_files, options)
    
    if options.check_md5:
        local_files = filter_compare_md5(local_files, mirror_files, config,
                                         options)
    else:
        local_files = remove_in_mirror_files(local_files, mirror_files)

    return local_files

def remove_not_in_local_files(mirror_files, local_files):
    filtered_mirror_files = []
    for file in mirror_files:
        if file[-4:] == '.md5':
            if file[:-4] in local_files:
                filtered_mirror_files.append(file)
        else:
            if file in local_files:
                filtered_mirror_files.append(file)
    return filtered_mirror_files


def filter_mirror_files_md5_sanity(mirror_files, local_files, options):
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
            if options.interactive:
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


def filter_compare_md5(local_files, mirror_files, config, options):

    filtered_local_files = []
    for file in local_files:
        md5_file = file + '.md5'
        if not md5_file in mirror_files:
            filtered_local_files.append(file)
        else:
            mirror_md5 = subprocess.Popen(
                ['ssh', config.get('mirror', 'put_hostname'),
                 'cat',
                 os.path.join(config.get('mirror', 'put_path'), md5_file)],
                stdout=subprocess.PIPE).communicate()[0]
            with open(md5_file, "r") as local_md5_file:
                local_md5 = local_md5_file.readline()
            if local_md5 == mirror_md5:
                continue
            else:
                print "\nWARNING: md5 mismatch for %s"%file
                print 'local md5  =', local_md5
                print 'mirror md5 =', mirror_md5
                if options.interactive:
                    while True:
                        answer = raw_input(
                            "(s)kip file, (o)verwrite mirror copy, (g)et mirror copy: ")
                        if answer == 's':
                            break
                        elif answer == 'o':
                            filtered_local_files.append(file)
                            break
                        elif answer == 'g':
                            print "WARNING: get not implemented"
                            break
                        else:
                            continue
    return filtered_local_files


def remove_in_mirror_files(local_files, mirror_files):
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
