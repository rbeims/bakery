from __future__ import with_statement # This isn't required in Python 2.6
import oebakery, optparse, ConfigParser, os, re, sys, shutil

class TmpCommand:

    def __init__(self, config, argv=[]):

        parser = optparse.OptionParser("""Usage: oe tmp [option] [name]*

Manage OpenEmbedded TMPDIR's

  oe tmp                      show available tmp areas
  oe tmp <name>		      select tmp area
  oe tmp -c|--create <name>   create (and select) tmp area
  oe tmp -d|--delete <name>*  delete tmp area(s)""")

        parser.add_option("-c", "--create",
                          action="store_true", dest="create", default=False,
                          help="create new tmp area")

        parser.add_option("-d", "--delete",
                          action="store_true", dest="delete", default=False,
                          help="delete tmp area")

        (self.options, self.args) = parser.parse_args(argv)

        if ((self.options.create and self.options.delete)
            or (self.options.create and len(self.args) != 1)
            or (self.options.delete and len(self.args) < 1)):
            print >>sys.stderr, 'Invalid arguments'
            parser.print_help()
            sys.exit(1)

        for arg in self.args:
            if '/' in arg:
                print >>sys.stderr, 'invalid tmp name:', arg
                sys.exit(1)

        self.config = config

        if self.config.has_option('tmp', 'basedir'):
            self.basedir = os.path.normpath(
                os.path.join(oebakery.get_topdir(),
                             self.config.get('tmp', 'basedir')))
        else:
            self.basedir = None

        self.tmpdir = os.path.normpath(
            os.path.join(oebakery.get_topdir(),
                         self.config.get('tmp', 'tmpdir')))

        return


    def get_tmpdir(self):

        if os.path.exists(self.tmpdir):
            return os.path.realpath(self.tmpdir)

        if self.basedir:
            if not os.path.exists(self.basedir):
                os.makedirs(self.basedir)
            self.create_tmp_area(self.config.get('tmp', 'default'))

        else:
            os.makedirs(self.tmpdir)

        return os.path.realpath(self.tmpdir)


    def run(self):

        if not self.basedir:
            print >>sys.stderr, 'Error: no tmp.basedir specified'
            sys.exit(1)

        if not os.path.exists(self.basedir):
            os.makedirs(self.basedir)

        if self.options.create:
            self.create_tmp_area(self.args[0])

        elif self.options.delete:
            for tmp in self.args:
                self.delete_tmp_area(tmp)
            return

        elif len(self.args) == 0:
            return self.show_tmp_areas()

        else:
            return self.select_tmp_area(self.args[0])


    def create_tmp_area(self, name):

        areadir = os.path.join(self.basedir, name)

        if not os.path.exists(areadir):
            os.makedirs(areadir)

        return self.select_tmp_area(name)


    def select_tmp_area(self, name):

        areadir = os.path.join(self.basedir, name)

        if not os.path.exists(areadir):
            print >>sys.stderr, 'no such directory:', areadir
            print >>sys.stderr, 'you can create it with'
            print >>sys.stderr, '  oe tmp -c', name
            return

        if os.path.exists(self.tmpdir) and not os.path.islink(self.tmpdir):
            print >>sys.stderr, 'not a symlink:', self.tmpdir

        if os.path.islink(self.tmpdir):
            os.remove(self.tmpdir)

        try:
            arealink = os.path.relpath(areadir, os.path.dirname(self.tmpdir))
        except AttributeError:
            arealink = areadir
        os.symlink(arealink, self.tmpdir)

        return


    def delete_tmp_area(self, name):

        areadir = os.path.join(self.basedir, name)

        if not os.path.exists(areadir):
            print 'no such directory:', areadir
            return

        real_tmpdir = os.path.realpath(self.tmpdir)
        real_areadir = os.path.realpath(areadir)
        if real_areadir == real_tmpdir:
            print >>sys.stderr, 'Error: cannot delete active tmp area'
            sys.exit(1)

        if os.path.islink(areadir):
            areadir = os.path.realpath(areadir)

        shutil.rmtree(areadir)

        return


    def show_tmp_areas(self):

        if not self.basedir:
            print >>sys.stderr, 'Error: no tmp.basedir specified'
            sys.exit(1)

        if not os.path.isdir(self.basedir):
            return

        real_tmpdir = os.path.realpath(self.tmpdir)

        for areadir in sorted(os.listdir(self.basedir)):
            real_areadir = os.path.realpath(
                os.path.join(self.basedir, areadir))
            if not os.path.isdir(real_areadir):
                continue
            if real_areadir == real_tmpdir:
                print '*', os.path.basename(areadir)
            else:
                print ' ', os.path.basename(areadir)

        return
