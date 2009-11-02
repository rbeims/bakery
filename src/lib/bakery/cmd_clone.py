import optparse, sys, os
import bakery
from bakery.cmd_init import InitCommand

class CloneCommand:

    def __init__(self, argv):

        parser = optparse.OptionParser("""Usage: oe clone [options]* <repository> [directory]

  Clone OE Bakery development environment into a new directory.

Arguments:
  file        bakery configuration file (remote URL or local file)
  directory   directory to clone into (default is current directory)""")

        (options, args) = parser.parse_args(argv)

        if len(args) < 1:
            parser.error("too few arguments")
        if len(args) > 2:
            parser.error("too many arguments")

        self.repository = args[0]

        if len(args) == 2:
            self.directory = args[1]
        else:
            self.directory = os.path.basename(self.repository)
            if self.directory[-4:] == '.git':
                self.directory = self.directory[:-4]

        self.options = options

        return


    def run(self):

        if not bakery.call("git clone %s %s"%(self.repository, self.directory)):
            return

        os.chdir(self.directory)

        self.init_cmd = InitCommand(argv=[])

        return self.init_cmd.run()

