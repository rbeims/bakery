from confparse import ConfParser
import os

class BBParser(ConfParser):

    def __init__(self, data=None, parent=None, **kwargs):
        super(BBParser, self).__init__(data, parent, **kwargs)
        return

    # Override/allow addtask statements

    def p_addtask(self, p):
        '''addtask : addtask_task
                   | addtask_task addtask_dependencies'''
        print "p_addtask TBD"
        return


    # Override/allow inherit statements

    def p_inherit(self, p):
        '''inherit : INHERIT inherit_classes'''
        print "p_inherit TBD"
        return

    def inherit(self, classes):
        __inherit_cache = self.data.getVar("__inherit_cache") or []

        for filename in classes:
            print "inherit class=%s"%(filename)
            filename = self.data.expand(filename)

            if (not os.path.isabs(filename) and
                not filename.endswith(".bbclass")):
                    filename = os.path.join("classes", "%s.bbclass"%(filename))

            if filename in __inherit_cache:
                return
            __inherit_cache.append(filename)
            self.data.setVar("__inherit_cache", __inherit_cache)

            print "inherit filename=%s"%(filename)
            self.include(self.data, filename, require=True)

            __inherit_cache = self.data.getVar("__inherit_cache")

        return


    # Override/allow function definitions

    def p_func(self, p):
        '''func : VARNAME FUNCSTART func_body FUNCSTOP'''
        self.data.setVar(p[1], p[3])
        self.data.setVarFlag(p[1], 'func', 'sh')
        p[0] = p[1]
        return

    def p_python_func(self, p):
        '''python_func : PYTHON func'''
        self.data.setVarFlag(p[2], 'func', 'python')
        return

    def p_fakeroot_func(self, p):
        '''fakeroot_func : FAKEROOT func'''
        self.data.setVarFlag(p[2], 'fakeroot', True)
        return
