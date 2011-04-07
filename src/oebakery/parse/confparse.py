import ply.lex, ply.yacc
import os
import bb.utils
from oebakery.parse import ParseError

class ConfParser(object):

    def __init__(self, data=None, parent=None):
        self.tokens = tuple(set(self.tokens +
                                list(self.reserved.values()) +
                                list(self.addtask_reserved.values())))
        self.lexer = ply.lex.lex(module=self)
        tabmodule = self.__class__.__module__ + "_tab"
        self.yacc = ply.yacc.yacc(module=self,
                                    tabmodule=tabmodule, debug=0)
        if data is not None:
            self.data = data
        else:
            self.data = oebakery.data.sqlite.SqliteData()
        self.parent = parent
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

    precedence = ()

    literals = ''

    states = (
        ('def', 'exclusive'),
        ('func', 'exclusive'),
        ('include', 'exclusive'),
        ('inherit', 'exclusive'),
        ('addtask', 'exclusive'),
        )

    tokens = [
        'VARNAME', 'FLAG',
        'ASSIGN', 'EXPASSIGN', 'WEAKASSIGN', 'LAZYASSIGN',
        'APPEND', 'PREPEND', 'POSTDOT', 'PREDOT',
        'STRING',
        'NEWLINE', 'COMMENT',
        'INCLUDEFILE', # 'INCLUDE' and 'REQUIRE' included as reserved word
        'INHERITCLASS', # 'INHERIT' included as reserved word
        'FUNCSTART', 'FUNCSTOP', 'FUNCLINE', 'DEF',
        'TASK',
        ]


    def t_DEF(self, t):
        r'def[ \t]+[a-zA-Z][a-zA-Z0-9_]*[ \t]*\(.*\):\n'
        t.lexer.lineno += 1
        t.lexer.push_state('def')
        print "DEF=%s"%(repr(t.value))
        return t

    t_def_ignore = ''

    def t_def_FUNCLINE(self, t):
        r'[ \t]+[^\n]*\n'
        t.lexer.lineno += 1
        print "FUNCLINE=%s"%(repr(t.value))
        return t

    def t_def_FUNCSTOP(self, t):
        r'\n'
        t.lexer.lineno += 1
        t.lexer.pop_state()
        print "FUNCSTOP=%s"%(repr(t.value))
        return t


    def t_INCLUDE(self, t):
        r'include[ \t]'
        t.lexer.push_state('include')
        return t

    def t_REQUIRE(self, t):
        r'require[ \t]'
        t.lexer.push_state('include')
        return t

    t_include_ignore = ' \t'

    def t_include_INCLUDEFILE(self, t):
        r'[^ \t]+'
        return t

    def t_include_NEWLINE(self, t):
        r'\n'
        t.lexer.lineno += 1
        t.lexer.pop_state()
        return t


    def t_INHERIT(self, t):
        r'inherit[ \t]'
        t.lexer.push_state('inherit')
        return t

    t_inherit_ignore = ' \t'

    def t_inherit_INHERITCLASS(self, t):
        r'[a-zA-Z0-9\-_]+'
        return t

    def t_inherit_NEWLINE(self, t):
        r'\n'
        t.lexer.lineno += 1
        t.lexer.pop_state()
        return t


    def t_FUNCSTART(self, t):
        r'\(\)[ \t]*\{[ \t]*\n'
        t.lexer.funcstart = t.lexer.lineno
        t.lexer.push_state('func')
        t.lexer.lineno += 1
        return t

    t_func_ignore = ""

    def t_func_FUNCSTOP(self, t):
        r'\}'
        t.lexer.pop_state()
        return t

    def t_func_FUNCLINE(self, t):
        r'.*\n'
        t.lexer.lineno += 1
        return t

    def t_ADDTASK(self, t):
        r'addtask[ \t]'
        t.lexer.push_state('addtask')
        return t

    t_addtask_ignore = ' \t'

    addtask_reserved = {
        'after'		: 'AFTER',
        'before'	: 'BEFORE',
        }

    def t_addtask_TASK(self, t):
        r'[a-zA-Z_]+'
        t.type = self.addtask_reserved.get(t.value, 'TASK')
        return t

    def t_addtask_NEWLINE(self, t):
        r'\n'
        t.lexer.lineno += 1
        t.lexer.pop_state()
        return t


    def t_TRUE(self, t):
        r'True'
        t.type = "STRING"
        t.value = "1"
        return t

    def t_FALSE(self, t):
        r'False'
        t.type = "STRING"
        t.value = "0"
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.type = "STRING"
        return t


    def t_VARNAME(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_\-\${}/]*'
        t.type = self.reserved.get(t.value, 'VARNAME')
        return t

    def t_FLAG(self, t):
        r'\[[a-z][a-z_]*\]'
        t.type = self.reserved.get(t.value, 'FLAG')
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
        raise SyntaxError("Unterminated string", t.lineno)

    def t_UNTERMINATEDSQUOTESTRING(self, t):
        r"'(\\'|\\\n|[^'\n])*?\n"
        t.lineno += t.value.count('\n')
        raise SyntaxError("Unterminated string", t.lineno)



    def t_COMMENT(self, t):
        r'\#[^\n]*'
        pass # no return value, token discarded

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        return t

    t_ignore = ' \t'


    def lextest(self, data, debug=False):
        self.lexer.input(data)
        tokens = []
        for tok in self.lexer:
            if debug:
                print tok.type, repr(tok.value), tok.lineno, tok.lexpos
            tokens.append((tok.type, tok.value))
        return tokens


    start = 'syntax'


    def p_syntax(self, p):
        '''syntax : statement
                  | statement syntax'''
        return

    def p_statement(self, p):
        '''statement : NEWLINE
                     | assignment NEWLINE
                     | export_variable NEWLINE
                     | include NEWLINE
                     | require NEWLINE
                     | inherit NEWLINE
                     | func NEWLINE
                     | fakeroot_func NEWLINE
                     | python_func NEWLINE
                     | def_func
                     | addtask NEWLINE
                     | COMMENT'''
        return

    def p_variable(self, p):
        '''variable : VARNAME
                    | export_variable'''
        p[0] = (p[1], '')
        return

    def p_export_variable(self, p):
        '''export_variable : EXPORT VARNAME'''
        self.data.setVarFlag(p[2], 'export', "1")
        p[0] = p[2]
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

    def p_include(self, p):
        '''include : INCLUDE INCLUDEFILE'''
        self.include(p[2])
        return

    def p_require(self, p):
        '''require : REQUIRE INCLUDEFILE'''
        self.include(p[2], require=True)
        return

    def p_inherit(self, p):
        '''inherit : INHERIT inherit_classes'''
        raise SyntaxError("inherit statements not allowed in configuration files")

    def p_inherit_classes(self, p):
        '''inherit_classes : INHERITCLASS'''
        p[0] = [ p[1] ]
        return

    def p_inherit_classes2(self, p):
        '''inherit_classes : INHERITCLASS inherit_classes'''
        p[0] = p[1].append(p[2])
        return

    def p_addtask(self, p):
        '''addtask : addtask_task
                   | addtask_task addtask_dependencies'''
        raise ParseError(self, "addtask not allowed in configuration files: "
                         "%s line %d"%(self.filename or "<unknown>", p.lineno+1),
                         p)

    def taskname(self, s):
        if s.startswith("do_"):
            return "do_" + s
        return s

    def p_addtask_task(self, p):
        '''addtask_task : ADDTASK TASK'''
        p[0] = self.taskname(p[1])
        return

    def p_addtask_dependencies1(self, p):
        '''addtask_dependencies : addtask_dependency'''
        p[0] = p[1]
        return

    def p_addtask_dependencies2(self, p):
        '''addtask_dependencies : addtask_dependency addtask_dependencies'''
        p[0] = (set(p[1][0] + p[2][0]), set(p[1][1] + p[2][1]))
        return

    def p_addtask_dependency(self, p):
        '''addtask_dependency : addtask_after
                              | addtask_before'''
        p[0] = p[1]
        return

    def p_addtask_after(self, p):
        '''addtask_after : AFTER tasks'''
        p[0] = (p[2], [])
        return

    def p_addtask_before(self, p):
        '''addtask_before : BEFORE tasks'''
        p[0] = ([], p[2])
        return

    def p_tasks(self, p):
        '''tasks : TASK'''
        p[0] = [ self.taskname(p[1]) ]
        return

    def p_tasks2(self, p):
        '''tasks : TASK tasks'''
        p[0] = [ self.taskname(p[1]) ] + p[2]
        return

    def p_func(self, p):
        '''func : VARNAME FUNCSTART func_body FUNCSTOP'''
        raise SyntaxError("functions not allowed in configuration files")

    def p_func_body(self, p):
        '''func_body : FUNCLINE
                     | FUNCLINE func_body'''
        p[0] = p[1]
        if len(p) > 2:
            p[0] += p[2]
        return

    def p_fakeroot_func(self, p):
        '''fakeroot_func : FAKEROOT func'''
        raise SyntaxError("functions not allowed in configuration files")

    def p_python_func(self, p):
        '''python_func : PYTHON func'''
        raise SyntaxError("functions not allowed in configuration files")

    def p_def_func(self, p):
        '''def_func : DEF func_body FUNCSTOP'''
        raise SyntaxError("functions not allowed in configuration files")


    def t_ANY_error(self, t):
        #print "Illegal character in %s at line %d: %s"%(
        #    self.filename or "<unknown>", t.lineno+1, repr(t.value[0]))
        #self.syntax_error(t, 1)
        #raise SyntaxError("Illegal character '%s'"%(t.value[0]))
        raise ParseError(self, "Illegal character in %s at line %d: %s"%(
                self.filename or "<unknown>", t.lineno+1, repr(t.value[0])),
            t, t.value[0])

    def p_error(self, p):
        #print "Syntax error in %s at line %d: type=%s value=%s"%(
        #    self.filename or "<unknown>", p.lineno+1, p.type, p.value)
        #self.syntax_error(p)
        #raise SyntaxError("Syntax error: %s"%(repr(p)))
        raise ParseError(self,
            "Syntax error in %s at line %d: type=%s value=%s"%(
                self.filename or "<unknown>", p.lineno+1, p.type, p.value),
                         p, p.value)

    def syntax_error(self, err, errlen=None):
        if not errlen:
            errlen = len(err.value)
        firstline = max(err.lineno - 5, 0)
        lastline = min(err.lineno + 5, len(self.lines) - 1)
        errlinepos = 0
        for lineno in xrange(err.lineno):
            errlinepos += len(self.lines[lineno]) + 1
        errpos = (err.lexpos - 1) - errlinepos
        errlinebefore = self.lines[err.lineno][:(err.lexpos - errlinepos)]
        errlinebefore = len(errlinebefore.expandtabs())
        linenofmtlen = len(str(lastline))
        lineprintfmt = "%%s%%%dd %%s"%(linenofmtlen)
        for lineno in xrange(firstline, lastline):
            if lineno == err.lineno:
                if lineno:
                    print ""
                prefix = "-> "
            else:
                prefix = "   "
            print lineprintfmt%(prefix, lineno + 1,
                                self.lines[lineno].expandtabs())
            if lineno == err.lineno:
                prefixlen = len(prefix) + linenofmtlen + 1
                print "%s%s"%(" "*(prefixlen + errlinebefore),
                              "^"*errlen)
        if self.parent:
            parent = self.parent
            print "Included from %s"%(parent.filename)
            parent = parent.parent
            while parent:
                print "              %s"%(parent.filename)
        return


    def inherit(self, filename):
        if not os.path.isabs(filename) and not filename.endswith(".bbclass"):
            filename = os.path.join("classes", "%s.bbclass"%(filename))
        if not "__INHERITS" in self.data:
            self.data["__INHERITS"] = filename
        else:
            __INHERITS = self.data["__INHERITS"]
            if filename in __INHERITS.split():
                return
            self.data.appendVar("__INHERITS", filename)
        self.include(filename, require=True)


    def include(self, filename, require=False):
        filename = self.data.expand(filename)
        print "including file=%s"%(filename)
        parser = self.__class__(self.data, parent=self)
        rv = parser.parse(filename, require, parser)
        return rv


    def parse(self, filename, require=True, parser=None):
        if not os.path.isabs(filename):
            bbpath = self.data.getVar("BBPATH", 2)
            if self.parent:
                print "parent=%s parent.filename=%s"%(self.parent, self.parent.filename)
                dirname = os.path.dirname(self.parent.filename)
                bbpath = "%s:%s"%(dirname, bbpath)
            filename = bb.utils.which(bbpath, filename)
        else:
            if not os.path.exists(filename):
                print "file not found: %s"%(filename)
                return

        if filename:
            self.filename = os.path.realpath(filename)
        else:
            self.filename = ""

        if not os.path.exists(self.filename):
            if not require:
                return
            else:
                print "required file could not be included"
                return

        if self.parent:
            oldfile = os.path.realpath(self.filename[-1])
            if self.filename == oldfile:
                print "don't include yourself!"
                return

        mtime = os.path.getmtime(self.filename)
        f = open(self.filename)
        self.text = f.read()
        f.close()
        self.data.setFileMtime(self.filename, mtime)

        if not parser:
            parser = self
        return parser._parse(self.text)


    def _parse(self, s):
        self.lexer.lineno = 0
        self.yacc.parse(s + '\n', lexer=self.lexer)
        return self.data


    def yacctest(self, s):
        self.data = oebakery.data.sqlite.SqliteData()
        return self._parse(s)
