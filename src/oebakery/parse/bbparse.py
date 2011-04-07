from confparse import ConfParser
import os, string

class BBParser(ConfParser):

    def __init__(self, data=None, parent=None, **kwargs):
        super(BBParser, self).__init__(data, parent, **kwargs)
        return

    # Override/allow addtask statements

    def p_addtask(self, p):
        '''addtask : addtask_task'''
        self.data.setVarFlag(p[1], "task", True)
        self.data.appendVar("__BBTASKS", p[1])
        return

    def p_addtask2(self, p):
        '''addtask : addtask_task addtask_dependencies'''
        self.p_addtask(p)
        for after_task in p[2][0]:
            self.data.appendVarFlag(p[1], "after_task", after_task)
        for before_task in p[2][1]:
            self.data.appendVarFlag(p[1], "before_task", before_task)
            print "FIXME: add code to move before_task info to after_task in finalize"
        return


    # Override/allow inherit statements

    def p_inherit(self, p):
        '''inherit : INHERIT inherit_classes'''
        for inherit_class in p[2]:
            self.inherit(inherit_class)
        return


    # Override/allow function definitions

    def p_def_func(self, p):
        '''def_func : DEF func_body FUNCSTOP'''
        self.data.setVar(p[1], p[3])
        self.data.setVarFlag(p[1], 'func', 'sh')
        p[0] = p[1]
        return

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

    def p_python_anonfunc(self, p):
        '''python_func : PYTHON FUNCSTART func_body FUNCSTOP'''
        funcname = "__anon_%s_%d"%(self.filename.translate(
                string.maketrans('/.+-', '____')), p.lexer.funcstart + 1)
        self.data.setVar(funcname, p[3])
        self.data.setVarFlag(funcname, 'func', 'python')
        self.data.setVarFlag(funcname, 'anon', True)
        return

    def p_fakeroot_func(self, p):
        '''fakeroot_func : FAKEROOT func'''
        self.data.setVarFlag(p[2], 'fakeroot', True)
        return
