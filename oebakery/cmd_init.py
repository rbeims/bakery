import os, subprocess, socket, shutil, optparse
import oebakery

class InitCommand:

    def __init__(self, argv=None):

        parser = optparse.OptionParser("""Usage: oe init [options]

  Setup OE Bakery development environment in the current directory.""")

        (self.options, self.args) = parser.parse_args(argv)

        self.config = oebakery.read_config()

        return


    def run(self):

        if not os.path.exists('.git'):
            if not oebakery.call("git init"):
                print 'Failed to initialize git'
                return

        if self.config.has_section('remotes'):
            for (name, url) in self.config.items('remotes'):
                oebakery.git_add_remote(name, url)

        if self.config.has_section('submodules'):
            for (path, url) in self.config.items('submodules'):
                section_name = "remotes '%s'"%path
                if self.config.has_section(section_name):
                    remotes = self.config.items(section_name)
                else:
                    remotes = None
                oebakery.git_add_submodule(path, url, remotes)

        return


    def init_bitbake(self):
    
        if os.path.exists("bitbake"):
            print "Skipping clone of bitbake"
    
        else:
            if not oebakery.call("git clone -o %s %s bitbake"%(
                    self.config.get("bitbake", "origin"),
                    self.config.get("bitbake", "repository"))):
                return

        os.chdir("bitbake")
        oebakery.call("git checkout -q %s"%(
                self.config.get("bitbake", "version")))
        os.chdir("..")
    
        return
            
    
    def init_metadata(self):

        if os.path.exists(self.config.get("metadata", "directory")):
            print "Skipping clone of %s"%(
                self.config.get("metadata", "directory"))
    
        else:
            if not oebakery.call("git clone -o %s %s %s"%(
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
                if oebakery.call("git remote add %s %s"%(
                        remote_name, self.config.get("metadata", option))):
                    update = True

        if update:
            oebakery.call("git remote update")

        os.chdir("..")

        return
