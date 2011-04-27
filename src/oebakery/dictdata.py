class DictData:

    def __init__(self):
        self._dict = {}
        self.mtime = {}
        return

    def dict(self):
        return self._dict

    def createCopy(self):
        import copy
        return copy.copy(self)

    def appendVarFlag(self, var, flag, value, separator=" "):
        current = self.getVarFlag(var, flag)
        if current == None:
            self.setVarFlag(var, flag, value)
        else:
            self.setVarFlag(var, flag, current + separator + value)

    def appendVar(self, var, value, separator=" "):
        current = self.getVar(var)
        if current == None:
            self.setVar(var, value)
        else:
            self.setVar(var, current + separator + value)

    def prependVarFlag(self, var, flag, value, separator=" "):
        current = self.getVarFlag(var, flag)
        if current == None:
            self.setVarFlag(var, flag, value)
        else:
            self.setVarFlag(var, flag, value + separator + current)

    def prependVar(self, var, value, separator=" "):
        current = self.getVar(var)
        if current == None:
            self.setVar(var, value)
        else:
            self.setVar(var, value + separator + current)

    def getVar(self, var, expand=2):
        val = self.getVarFlag(var, "")
        if expand and val:
            val = self.expand(val, expand in (1, True))
        return val

    def setVar(self, var, value, expand=0):
        return self.setVarFlag(var, "", value)

    def getVarFlag(self, var, flag):
        try:
            return self._dict[var][flag]
        except KeyError:
            return None

    def setVarFlag(self, var, flag, value):
        if not var in self._dict:
            self._dict[var] = {}
        self._dict[var][flag] = value
        return

    def delVarFlag(self, var, flag):
        try:
            del self._dict[var][flag]
        except KeyError:
            pass
        return

    def getVar(self, var, expand=2):
        val = self.getVarFlag(var, "")
        if expand and val:
            val = self.expand(val, expand in (1, True))
        return val

    def setVar(self, var, value, expand=0):
        return self.setVarFlag(var, "", value)

    def delVar(self, var):
        try:
            del self._dict[var]
        except KeyError:
            pass
        return

    def expand(self, val, allow_unexpand=False):
        if not val:
            return val
        expandparser = oebakery.parse.expandparse.ExpandParser(self, allow_unexpand)
        expval = expandparser.expand(val)
        return expval

    def setFileMtime(self, filename, mtime):
        self.mtime[filename] = mtime

    def getFileMtime(self, filename):
        if not filename in self.mtime:
            return None
        return self.mtime[filename]

    def __str__(self):
        return repr(self._dict)

    def __iter__(self):
        return self._dict.__iter__

    def __len__(self):
        return len(self._dict.keys())

    def __contains__(self, var):
        val = self.getVar(var, 0)
        return val is not None

    def __getitem__(self, var):
        return self.getVar(var, 0)
        
    def __setitem__(self, var, val):
        self.setVar(var, val)

    def __delitem__(self, var):
        self.delVar(var)


import ply.lex, ply.yacc
import re

class ExpandParser(object):

    def __init__(self, data, allow_unexpand=False):
        self.lexer = ply.lex.lex(module=self)
        self.parser = ply.yacc.yacc(module=self,
                                    tabmodule="expandparse_tab", debug=0)
        self.data = data
        self.allow_unexpand = allow_unexpand
        return


    def set_data(self, data):
        self.data = data
        return

    def set_allow_unexpand(self, allow_unexpand):
        self.allow_unexpand = allow_unexpand
        return


    literals = ''

    tokens = (
        'CHARS',
        'VAROPEN', 'VARNAME', 'VARCLOSE',
        'PYTHONOPEN', 'PYTHONCLOSE',
        )

    states = (
        ('var', 'exclusive'),
        ('python', 'exclusive'),
        )


    def t_INITIAL_var_PYTHONOPEN(self, t):
        r'\${@'
        t.lexer.push_state('python')
        return t

    def t_ANY_VAROPEN(self, t):
        r'\${'
        t.lexer.push_state('var')
        return t


    def t_python_PYTHONCLOSE(self, t):
        r'}'
        t.lexer.pop_state()
        return t


    def t_var_VARCLOSE(self, t):
        r'}'
        t.lexer.pop_state()
        return t

    def t_var_VARNAME(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        return t


    def t_INITIAL_python_CHARS(self, t):
        #r'([^\$]|\\\$)+'
        r'[^\\\$}]+'
        return t

    def t_INITIAL_python_SPECIALCHAR(self, t):
        r'[\\\$}]'
        t.type = 'CHARS'
        return t


    def t_ANY_error(self, t):
        raise SyntaxError("Illegal character '%s'"%(t.value[0]))

    t_ANY_ignore = ''

    start = 'syntax'

    def p_syntax1(self, p):
        '''syntax : string'''
        p[0] = p[1]
        return

    def p_syntax2(self, p):
        '''syntax : string syntax'''
        print "syntax2 %s %s"%(repr(p[1]), repr(p[2]))
        p[0] = p[1] + p[2]
        return

    def p_string(self, p):
        '''string : chars
                  | variable
                  | python'''
        p[0] = p[1]
        return

    def p_chars1(self, p):
        '''chars : CHARS'''
        p[0] = p[1]
        return

    def p_chars2(self, p):
        '''chars : CHARS chars'''
        p[0] = p[1] + p[2]
        return

    def p_variable(self, p):
        '''variable : VAROPEN varname VARCLOSE'''
        print "expanding %s"%(p[2])
        p[0] = self.data.getVar(p[2], [1,2][self.allow_unexpand])
        return

    def p_varname1(self, p):
        '''varname : varnamepart'''
        p[0] = p[1]
        return

    def p_varname2(self, p):
        '''varname : varnamepart varname'''
        p[0] = p[1] + p[2]
        return

    def p_varnamepart1(self, p):
        '''varnamepart : VARNAME'''
        p[0] = p[1]
        return

    def p_varnamepart2(self, p):
        '''varnamepart : variable'''
        if not re.match(self.t_var_VARNAME.__doc__ + '$', p[1]):
            raise ValueError(p[1])
        p[0] = p[1]
        return

    def p_python(self, p):
        '''python : PYTHONOPEN syntax PYTHONCLOSE'''
        print "python code: %s"%(repr(p[2]))
        val = better_eval(p[2], {'d': self.data})
        p[0] = self.data.expand(val, self.allow_unexpand)
        return


    def p_error(self, p):
        print "p_error"
        raise SyntaxError("Syntax error: %s"%(repr(p)))


    def expand(self, s):
        return self.parser.parse(s, lexer=self.lexer)
