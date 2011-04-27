import ply.lex, ply.yacc
import os
from dictdata import DictData

class SimpleParser(object):

    def __init__(self, data=None):
        self.lexer = ply.lex.lex(module=self)
        tabmodule = self.__class__.__module__ + "_tab"
        self.yacc = ply.yacc.yacc(module=self,
                                    tabmodule=tabmodule, debug=0)
        if data is not None:
            self.data = data
        else:
            self.data = DictData()
        return


    reserved = {
        'export'	: 'EXPORT',
        'require'	: 'REQUIRE',
        'include'	: 'INCLUDE',
        'inherit'	: 'INHERIT',
        'fakeroot'	: 'FAKEROOT',
        'python'	: 'PYTHON',
        'addtask'	: 'ADDTASK',
        }

    tokens = [
        'VARNAME', 'FLAG',
        'ASSIGN', 'EXPASSIGN', 'WEAKASSIGN', 'LAZYASSIGN',
        'APPEND', 'PREPEND', 'POSTDOT', 'PREDOT',
        'STRING',
        'NEWLINE', 'COMMENT',
        ]


    def t_VARNAME(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_\-\${}/]*'
        if self.reserved.get(t.value):
            raise ParseError(
                self, "Reserved word not allowed in simple configuration files",
                t, t.value)
        return t

    def t_FLAG(self, t):
        r'\[[a-z][a-z_]*\]'
        t.value = t.value[1:-1]
        return t


    def t_APPEND(self, t):
        r'\+='
        return t

    def t_PREDOT(self, t):
        r'\.='
        return t
    
    def t_LAZYASSIGN(self, t):
        r'\?\?='
        return t
    
    def t_WEAKASSIGN(self, t):
        r'\?='
        return t
    
    def t_EXPASSIGN(self, t):
        r':='
        return t

    def t_PREPEND(self, t):
        r'=\+'
        return t

    def t_POSTDOT(self, t):
        r'=\.'
        return t
    
    def t_ASSIGN(self, t):
        r'='
        return t

    
    def t_EMPTYSTRING(self, t):
        r'""|\'\''
        t.type = "STRING"
        t.value = ""
        return t

    def t_DQUOTESTRING(self, t):
        r'"(\\"|\\\n|[^"\n])*?"'
        t.type = "STRING"
        newlines = t.value.count('\n')
        if newlines:
            t.lineno += newlines
        t.value = t.value[1:-1].replace('\\\n','').replace('\\"','"')
        return t

    def t_SQUOTESTRING(self, t):
        r"'(\\'|\\\n|[^'\n])*?'"
        t.type = "STRING"
        t.lineno += t.value.count('\n')
        t.value = t.value[1:-1].replace('\\\n','').replace("\\'","'")
        return t


    def t_UNTERMINATEDDQUOTESTRING(self, t):
        r'"(\\"|\\\n|[^"\n])*?\n'
        t.lineno += t.value.count('\n')
        raise ParseError(self, "Unterminated string", t, t.value)

    def t_UNTERMINATEDSQUOTESTRING(self, t):
        r"'(\\'|\\\n|[^'\n])*?\n"
        t.lineno += t.value.count('\n')
        raise ParseError(self, "Unterminated string", t, t.value)


    def t_COMMENT(self, t):
        r'\#[^\n]*'
        pass # no return value, token discarded

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        return t

    t_ignore = ' \t'


    start = 'syntax'

    def p_syntax(self, p):
        '''syntax : statement
                  | statement syntax'''
        return

    def p_statement(self, p):
        '''statement : NEWLINE
                     | assignment NEWLINE
                     | COMMENT'''
        return

    def p_variable(self, p):
        '''variable : VARNAME'''
        p[0] = (p[1], '')
        return

    def p_flag(self, p):
        '''flag : VARNAME FLAG'''
        p[0] = (p[1], p[2])
        return

    def p_varflag(self, p):
        '''varflag : flag
                   | variable'''
        p[0] = p[1]
        return

    def p_simple_assignment(self, p):
        '''assignment : varflag ASSIGN STRING'''
        self.data.setVarFlag(p[1][0], p[1][1], p[3])
        return

    def p_exp_assignment(self, p):
        '''assignment : varflag EXPASSIGN STRING'''
        print "EXPASSIGN %s"%(p[1][0])
        self.data.setVarFlag(p[1][0], p[1][1], self.data.expand(p[3], 1))
        return

    def p_defaultval_assignment(self, p):
        '''assignment : variable LAZYASSIGN STRING'''
        self.data.setVarFlag(p[1][0], "defaultval", p[3])
        return

    def p_weak_assignment(self, p):
        '''assignment : varflag WEAKASSIGN STRING'''
        if self.data.getVarFlag(p[1][0], p[1][1]) == None:
            self.data.setVarFlag(p[1][0], p[1][1], p[3])
        return

    def p_append_assignment(self, p):
        '''assignment : varflag APPEND STRING'''
        self.data.appendVarFlag(p[1][0], p[1][1], p[3])
        return

    def p_prepend_assignment(self, p):
        '''assignment : varflag PREPEND STRING'''
        self.data.prependVarFlag(p[1][0], p[1][1], p[3])
        return

    def p_predot_assignment(self, p):
        '''assignment : varflag PREDOT STRING'''
        self.data.appendVarFlag(p[1][0], p[1][1], p[3], separator="")
        return

    def p_postdot_assignment(self, p):
        '''assignment : varflag POSTDOT STRING'''
        self.data.prependVarFlag(p[1][0], p[1][1], p[3], separator="")
        return

    def t_ANY_error(self, t):
        raise ParseError(self, "Illegal character in %s at line %d: %s"%(
                self.filename or "<unknown>", t.lineno+1, repr(t.value[0])),
                         t, t.value)

    def p_error(self, p):
        raise ParseError(
            self, "Syntax error in %s at line %d: type=%s value=%s"%(
                self.filename or "<unknown>", p.lineno+1, p.type, p.value),
            p, p.value)

    def parse(self, filename, require=True):
        self.filename = os.path.realpath(filename)

        if not os.path.exists(self.filename):
            print "No such file: %s"%(filename)
            return None

        mtime = os.path.getmtime(self.filename)
        f = open(self.filename)
        self.text = f.read()
        f.close()
        self.data.setFileMtime(self.filename, mtime)

        self.lexer.lineno = 0
        self.yacc.parse(self.text + '\n', lexer=self.lexer)

        return self.data


class ParseError(Exception):

    def __init__(self, parser, msg, details=None, symbol=None):
        self.parser = parser
        self.msg = msg
        self.details = details
        if not symbol and details:
            self.symbol = details.value
        else:
            self.symbol = symbol
        return

    def __str__(self):
        return self.msg

    def print_details(self):
        print self.msg
        if not self.details:
            return ""
        lines = self.parser.text.splitlines()
        firstline = max(self.details.lineno - 5, 0)
        lastline = min(self.details.lineno + 5, len(lines) - 1)
        errlinepos = 0
        for lineno in xrange(self.details.lineno):
            errlinepos += len(lines[lineno]) + 1
        errpos = (self.details.lexpos - 1) - errlinepos
        errlinebefore = lines[self.details.lineno]\
            [:(self.details.lexpos - errlinepos)]
        errlinebefore = len(errlinebefore.expandtabs())
        linenofmtlen = len(str(lastline))
        lineprintfmt = "%%s%%%dd %%s"%(linenofmtlen)
        for lineno in xrange(firstline, lastline):
            if lineno == self.details.lineno:
                if lineno:
                    print ""
                prefix = "-> "
            else:
                prefix = "   "
            print lineprintfmt%(prefix, lineno + 1,
                                lines[lineno].expandtabs())
            if lineno == self.details.lineno:
                prefixlen = len(prefix) + linenofmtlen + 1
                print "%s%s"%(" "*(prefixlen + errlinebefore),
                              "^"*len(self.symbol))
        return
