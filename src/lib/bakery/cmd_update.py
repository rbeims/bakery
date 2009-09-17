import os, subprocess, socket
from optparse import OptionParser

import bakery

class UpdateCommand:

    def __init__(self, argv, config):

        parser = OptionParser("""Usage: oe update [options]

  Update OE Bakery development environment in the current directory.""")

        parser.add_option("-b", "--bitbake",
                          action="append_const", dest="what", const="bitbake",
                          help="update BitBake repository")

        parser.add_option("-o", "--openembedded",
                          action="append_const", dest="what", const="openembedded",
                          help="update OpenEmbedded repository")

        (options, args) = parser.parse_args(argv)

        self.config = config
        self.options = options

        if options.what == None:
            options.what = ["bitbake", "openembedded"]

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

            self.update_bitbake(config)

        if "openembedded" in options.what:

            if not config.has_section("openembedded"):
                print "WARNING: no [openembedded] section in conf/oe.conf"
                config.add_section("openembedded")

            if not config.has_option("openembedded", "url"):
                config.set("openembedded", "url",
                           "git://git.openembedded.org/openembedded")
            if not config.has_option("openembedded", "origin_name"):
                config.set("openembedded", "origin_name", "origin")

            self.update_openembedded(config)

        return


    def update_bitbake(self, config):
    
        if os.path.exists("bitbake"):
            print "Skipping clone of bitbake"
    
        else:
            bakery.call("git clone -o %s %s bitbake"%(
                    config.get("bitbake", "origin_name"),
                    config.get("bitbake", "url")))
    
        return


    def init_openembedded(self, config):
    
        if os.path.exists("openembedded"):
            print "Skipping clone of openembedded"
    
        else:
            if (config.has_option("openembedded", "local_hostname") and
                config.has_option("openembedded", "local_url") and
                socket.gethostname() == config.get("openembedded",
                                                   "local_hostname")):
                url = config.get("openembedded", "local_url")
            else:
                url = config.get("openembedded", "url")
        
            bakery.call("git clone -o %s %s openembedded"%(
                    config.get("openembedded", "origin_name"), url))
    
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
                if bakery.call("git remote add %s %s"%(
                        remote, config.get(section, "url"))):
                    update = True

        if update:
            bakery.call("git remote update")

        return
