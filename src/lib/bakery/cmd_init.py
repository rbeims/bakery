import os, subprocess, socket
from optparse import OptionParser

import bakery

class InitCommand:

    def __init__(self, argv):

        parser = OptionParser("""Usage: oe init [options]

  Setup OE Bakery development environment in the current directory.""")

        parser.add_option("-f", "--file",
                          action="store", type="string", dest="file",
                          help="use configuration file FILE")

        parser.add_option("-b", "--bitbake",
                          action="append_const", dest="what", const="bitbake",
                          help="clone and configure BitBake")

        parser.add_option("-m", "--metadata",
                          action="append_const", dest="what", const="openembedded",
                          help="clone and configure metadata repositories")

        (options, args) = parser.parse_args(argv)

        if options.what == None:
            if len(args) == 0:
                options.what = ["bitbake", "metadata"]
            else:
                options.what = []

        for arg in args:
            options.what.append(arg)

        if options.file:
            print "--file not implemented: download and install file to conf/oe.conf"
            return

        config = bakery.read_config()

        self.options = options
        self.config = config

        if "bitbake" in options.what:

            if not config.has_section("bitbake"):
                print "WARNING: no [bitbake] section in conf/oe.conf"
                config.add_section("bitbake")

            if not config.has_option("bitbake", "url"):
                config.set("bitbake", "url",
                           "git://git.openembedded.org/bitbake")

            if not config.has_option("bitbake", "default"):
                config.set("bitbake", "default",
                           "branches/bitbake-1.8")
            if not config.has_option("bitbake", "origin_name"):
                config.set("bitbake", "origin_name", "origin")

        if "metadata" in options.what:

            self.prepare_metadata_sections()

        return


    def run(self):

        if "bitbake" in self.options.what:
            self.init_bitbake()

        if "metadata" in self.options.what:
            for section in self.metadata_sections:
                self.init_metadata(section)


    def init_bitbake(self):
    
        if os.path.exists("bitbake"):
            print "Skipping clone of bitbake"
    
        else:
            bakery.call("git clone -o %s %s bitbake"%(
                    self.config.get("bitbake", "origin_name"),
                    self.config.get("bitbake", "url")))
    
        return


    def prepare_metadata_sections(self):

        self.metadata_sections = []

        for section in self.config.sections():

            if (len(section) > len("meta:") and
                section[:len("meta:")] == "meta:"):

                if section[len("meta:"):] in ["bin", "lib", "conf", "bitbake",
                                              "ingredient", "prebake",
                                              "tmp", "scm"]:
                    print >>sys.stderr, "Invalid metadata section %s"%section
                    continue

                if not self.config.has_option(section, "url"):
                    print >>sys.stderr, "Metadata section %s has no url option"%section

                if not self.config.has_option(section, "origin_name"):
                    self.config.set(section, "origin_name", "origin")

                self.metadata_sections.append(section)

        return
            
    
    def init_metadata(self, section):

        meta_name = section[len("meta:"):]

        if os.path.exists(meta_name):
            print "Skipping clone of %s"%(meta_name)
    
        else:
            if not bakery.call("git clone -o %s %s %s"%(
                    self.config.get(section, "origin_name"),
                    self.config.get(section, "url"),
                    meta_name)):
                return
    
        if not os.chdir(meta_name):
            return

        update = False
        for option in self.config.options(section):

            if (len(option) > len("remote:") and
                option[:len("remote:")] == "remote:"):

                remote_name = option[len("remote:"):]

                if os.path.exists(".git/refs/remotes/%s"%(remote_name)):
                    print >>sys.stderr, "Remote %s already created"%(remote_name)
                    continue
                if bakery.call("git remote add %s %s"%(
                        remote_name, self.config.get(section, option))):
                    update = True

        if update:
            bakery.call("git remote update")

        os.chdir("..")

        return
