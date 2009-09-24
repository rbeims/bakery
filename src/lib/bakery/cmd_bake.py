import bakery, optparse, ConfigParser, os, re, sys

class BakeCommand:

    def __init__(self, config, argv):

        parser = optparse.OptionParser("""Usage: oe bake [bitbake options]

  Build recipes using BitBake in the current OpenEmbedded development
  environment.  This can be done from any subdirectory of the OpenEmbedded
  development environment.""")

#        (self.options, self.args) = parser.parse_args(argv)

        self.args = argv
        self.config = config
        self.topdir = bakery.get_topdir()
        self.metadir = config.get("metadata", "directory")

        return


    def setup_tmpdir(self):
        abi_version = bakery.get_simple_config_line(
            "%s/conf/abi_version.conf"%(self.metadir), "OELAYOUT_ABI")
        if abi_version == None:
            abi_version = 1
        else:
            abi_version = int(abi_version)

        tmpdir = "tmp"
        tmpdird = "tmp.d"

        if (os.path.exists(tmpdir) and not os.path.islink(tmpdir)):
            return os.path.realpath(tmpdir)

        if not os.path.exists(tmpdird):
            os.makedirs(tmpdird)

        if os.path.islink(tmpdir):
            os.remove(tmpdir)

        with open("%s/.git/HEAD"%(self.metadir)) as file:
            line = file.readline()
            regex = re.compile('ref: refs/heads/(.*)\n')
            match = regex.match(line)
            if match:
                branch = match.group(1)
            else:
                branch = "__UNKNOWN_BRANCH__"

        abi_tmpdir = os.path.realpath("%s/%s-abi%d"%(tmpdird, branch, abi_version))

        if not os.path.exists(abi_tmpdir):
            os.makedirs(abi_tmpdir)

        os.symlink(abi_tmpdir, tmpdir)

        self.tmpdir = abi_tmpdir        
        return abi_tmpdir


    def run(self):

        print "OE Bakery:", self.topdir

        print "BitBake:  ", self.config.get("bitbake", "version")
        print "BitBake version handling NOT IMPLEMENTED YET"
    
#    bitbake_min_version = None
#    if not os.path.exists(dot_bitbake_filename):
#        bitbake_min_version = get_simple_config_line(
#            "openembedded/conf/sanity.conf",
#            "BB_MIN_VERSION")
#        dot_bitbake_filename = "%s/.bitbake"%(self.topdir)
#        if not os.path.exists(dot_bitbake_filename):
#            print >>sys.stderr, "ERROR: could not determine which BitBake version to use"
#            return
#
#    with open(dot_bitbake_filename) as dot_bitbake_file:
#        bitbake_version = dot_bitbake_file.readline().rstrip()
#
#    if bitbake_min_version != None:
#        if (version_str_to_tuple(bitbake_min_version) >
#            version_str_to_tuple(bitbake_version)):
#            bitbake_version = "tags/bitbake-%s"%bitbake_min_version
#    
#    if not os.path.exists("bitbake/%s/bin"%(bitbake_version)):
#        print >>sys.stderr, "ERROR: could not find BitBake version %s"%(bitbake_version)

        self.setup_tmpdir()
        print "Temp dir: ", self.tmpdir

        metadir = "%s/%s"%(self.topdir, self.metadir)

        os.environ["OE_HOME"] = self.topdir
        os.environ["OE_TMPDIR"] = self.tmpdir
        os.environ["BBPATH"] = "%s:%s"%(self.topdir, metadir)
        os.environ["PATH"] = "%s/bitbake/bin:%s"%(
            self.topdir, os.environ["PATH"])

        if (os.path.exists("%s/recipes"%(metadir)) and
            os.path.exists("%s/packages"%(metadir))):
            print >>sys.stderr, "ERROR: found both a recipes and packages dir, what to do?"
            return
        elif os.path.exists("%s/recipes"%(metadir)):
            os.environ["OE_BBFILES"] = "%s/recipes/*/*.bb"%(metadir)
        elif os.path.exists("%s/packages"%(metadir)):
            os.environ["OE_BBFILES"] = "%s/packages/*/*.bb"%(metadir)
        else:
            print >>sys.stderr, "ERROR: could not find any BitBake recipes"
            return
        os.environ["BB_ENV_EXTRAWHITE"] = "OE_HOME OE_BBFILES OE_TMPDIR"

        bakery.call(["bitbake"] + self.args)

        return
