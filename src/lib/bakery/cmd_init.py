import os, subprocess, socket, shutil, optparse
import bakery

class InitCommand:

    def __init__(self, argv=None):

        parser = optparse.OptionParser("""Usage: oe init [options]

  Setup OE Bakery development environment in the current directory.""")

        parser.add_option("-b", "--bitbake",
                          action="append_const", dest="what", const="bitbake",
                          help="clone and configure BitBake repository")

        parser.add_option("-m", "--metadata",
                          action="append_const", dest="what", const="metadata",
                          help="clone and configure metadata repository")

        (options, args) = parser.parse_args(argv)

        if options.what == None:
            if len(args) == 0:
                options.what = ["bitbake", "metadata", "config"]
            else:
                options.what = []

        for arg in args:
            options.what.append(arg)

        config = bakery.read_config()

        self.options = options
        self.config = config

        return


    def run(self):

        if "bitbake" in self.options.what:
            self.init_bitbake()

        if "metadata" in self.options.what:
            self.init_metadata()

        return


    def init_bitbake(self):
    
        if os.path.exists("bitbake"):
            print "Skipping clone of bitbake"
    
        else:
            if not bakery.call("git clone -o %s %s bitbake"%(
                    self.config.get("bitbake", "origin"),
                    self.config.get("bitbake", "repository"))):
                return

        os.chdir("bitbake")
        bakery.call("git checkout %s"%(
                self.config.get("bitbake", "version")))
        os.chdir("..")
    
        return
            
    
    def init_metadata(self):

        if os.path.exists(self.config.get("metadata", "directory")):
            print "Skipping clone of %s"%(
                self.config.get("metadata", "directory"))
    
        else:
            if not bakery.call("git clone -o %s %s %s"%(
                    self.config.get("metadata", "origin"),
                    self.config.get("metadata", "repository"),
                    self.config.get("metadata", "directory"))):
                return
    
        os.chdir(self.config.get("metadata", "directory"))

        update = False
        for option in self.config.options("metadata"):

            if (len(option) > len("remote.") and
                option[:len("remote.")] == "remote."):

                remote_name = option[len("remote."):]

                if os.path.exists(".git/refs/remotes/%s"%(remote_name)):
                    print >>sys.stderr, "Remote %s already created"%(
                        remote_name)
                    continue
                if bakery.call("git remote add %s %s"%(
                        remote_name, self.config.get("metadata", option))):
                    update = True

        if update:
            bakery.call("git remote update")

        os.chdir("..")

        return
