import os, subprocess, socket, shutil, optparse
import bakery

class InitCommand:

    def __init__(self, argv):

        parser = optparse.OptionParser("""Usage: oe init [options]

  Setup OE Bakery development environment in the current directory.""")

        parser.add_option("-f", "--file",
                          action="store", type="string", dest="file",
                          help="use configuration file FILE")

        parser.add_option("-u", "--url",
                          action="store", type="string", dest="url",
                          help="download and use configuration file URL")

        parser.add_option("-b", "--bitbake",
                          action="append_const", dest="what", const="bitbake",
                          help="clone and configure BitBake repository")

        parser.add_option("-m", "--metadata",
                          action="append_const", dest="what", const="metadata",
                          help="clone and configure metadata repository")

        parser.add_option("-c", "--config",
                          action="append_const", dest="what", const="config",
                          help="download local.conf.sample and setup local.conf")

        (options, args) = parser.parse_args(argv)

        if options.what == None:
            if len(args) == 0:
                options.what = ["bitbake", "metadata"]
            else:
                options.what = []

        for arg in args:
            options.what.append(arg)

        if options.file:
            print "--file not implemented: download and install file to conf/bakery.ini"
            return

        if options.url:
            print "--url not implemented: download and install file to conf/bakery.ini"
            return

        config = bakery.read_config()

        self.options = options
        self.config = config

        return


    def run(self):

        if "bitbake" in self.options.what:
            self.init_bitbake()

        if "metadata" in self.options.what:
            self.init_metadata()

        if "config" in self.options.what:
            self.init_config()

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


    def init_config(self):

        if not self.config.has_option("config", "url"):
            return
        url = self.config.get("config", "url")

        wget_url = scp_url = None
        if (len(url) > len('scp://')) and (url[:len('scp://')] == 'scp://'):
            scp_url = url[len('scp://'):]
        else:
            wget_url = url

        if self.config.has_option("config", "wget_options"):
            wget_options = self.config.get("config", "wget_options")
        else:
            wget_options = ""

        if not os.path.exists("conf/local.conf.sample"):
            if wget_url:
                bakery.call("wget %s -O conf/local.conf.sample %s"%(
                    wget_options, wget_url))
            else:
                bakery.call("scp %s conf/local.conf.sample"%(scp_url))

        if not os.path.exists("conf/local.conf"):
            shutil.copyfile("conf/local.conf.sample", "conf/local.conf")
