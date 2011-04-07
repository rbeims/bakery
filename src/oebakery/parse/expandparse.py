import ply.lex, ply.yacc
import oebakery.data.sqlite
import re
from bb.utils import better_eval

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


    def lextest(self, data, debug=False):
        self.lexer.input(data)
        tokens = []
        for tok in self.lexer:
            if debug:
                print tok.type, repr(tok.value), tok.lineno, tok.lexpos
            tokens.append((tok.type, tok.value))
        return tokens

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


    def yacctest(self, s):
        self.data = oebakery.data.sqlite.SqliteData()
        self.parse(s)
        return self.data


    def expand(self, s):
        return self.parser.parse(s, lexer=self.lexer)
