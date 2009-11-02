import os, subprocess, socket, sys
import optparse

import oebakery

class UpdateCommand:

    def __init__(self, config, argv):

        parser = optparse.OptionParser("""Usage: oe update [options]

  Update OE Bakery development environment in the current directory.""")

        parser.add_option("-b", "--bitbake",
                          action="append_const", dest="what", const="bitbake",
                          help="update BitBake repository")

        parser.add_option("-m", "--metadata",
                          action="append_const", dest="what", const="metadata",
                          help="update metadata repository")

        (options, args) = parser.parse_args(argv)

        if options.what == None:
            if len(args) == 0:
                options.what = ["bitbake", "metadata"]
            else:
                options.what = []

        for arg in args:
            options.what.append(arg)

        self.config = config
        self.options = options

        return


    def run(self):

        if "bitbake" in self.options.what:
            self.update_bitbake()

        if "metadata" in self.options.what:
            self.update_metadata()

        return


    def update_bitbake(self):

        print >>sys.stderr, "INFO: bitbake update not implemented yet"
        return
    
        if not os.path.exists("bitbake"):
            print >>sys.stderr, "ERROR: bitbake not found!"
            return
    
        return


    def update_metadata(self):
    
        if not os.path.exists(self.config.get("metadata", "directory")):
            print >>sys.stderr, "ERROR: metadata directory not found: %s"%(
                self.config.get("metadata", "directory"))
    
        os.chdir(self.config.get("metadata", "directory"))

        oebakery.call("git pull")
        oebakery.call("git remote update")

        os.chdir("..")

        return
