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
