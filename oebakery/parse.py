import sys
import os
import ply.lex, ply.yacc

import oebakery
logger = oebakery.logger
import oebakery.gitmodules

class ParseError(Exception):

    def __init__(self, parser, msg, details=None, symbol=None, lineno=None):
        self.parser = parser
        self.msg = msg
        self.details = details
        if lineno is not None:
            self.errlineno = lineno
        elif "lexer" in dir(self.details):
            self.errlineno = self.details.lexer.lineno
        else:
            self.errlineno = self.details.lineno
        if symbol:
            self.symbol = symbol
        #elif self.details is None:
        #    self.symbol = ""
        elif not "value" in dir(self.details):
            self.symbol = None
        elif self.details.type == "error":
            self.symbol = self.details.value[0]
        else:
            self.symbol = self.details.value
        try:
            self.lexer = self.details.lexer
        except:
            self.lexer = self.parser.lexer
        if not self.symbol:
            self.msg += " in %s at line %d"%(
                parser.filename or "<unknown file>",
                self.lexer.lineno + 1)
        elif self.details.type == "error":
            self.msg += " in %s at line %d: %s"%(
                parser.filename or "<unknown file>",
                self.lexer.lineno + 1,
                repr(self.symbol))
        else:
            self.msg += " in %s at line %d: %s %s"%(
                parser.filename or "<unknown file>",
                self.lexer.lineno + 1,
                self.details.type, repr(self.symbol))
        return

    def __str__(self):
        return self.msg

    def print_details(self):
        print self.msg
        if not self.details:
            return ""
        lines = self.parser.text.splitlines()
        #errlineno = self.details.lineno
        #errlineno = self.lexer.lineno
        firstline = max(self.errlineno - 5, 0)
        lastline = min(self.errlineno + 5, len(lines))
        errlinepos = 0
        for lineno in xrange(self.errlineno):
            errlinepos += len(lines[lineno]) + 1
        #if isinstance(self.details, ply.lex.LexToken):
        #    print "this is a LexToken"
        #    lexpos = self.details.lexpos
        #elif isinstance(self.details, ply.lex.Lexer):
        #    print "this is a Lexer"
        #    lexpos = self.details.lexpos - len(self.symbol)
        try:
            lexpos = self.details.lexpos
            errpos = (lexpos - 1) - errlinepos
            errlinebefore = lines[self.errlineno]\
                [:(lexpos - errlinepos)]
            errlinebefore = len(errlinebefore.expandtabs())
        except AttributeError:
            lexpos = None
        linenofmtlen = len(str(lastline))
        lineprintfmt = "%%s%%%dd %%s"%(linenofmtlen)
        for lineno in xrange(firstline, lastline):
            if lineno == self.errlineno:
                if lineno:
                    print ""
                prefix = "-> "
            else:
                prefix = "   "
            print lineprintfmt%(prefix, lineno + 1,
                                lines[lineno].expandtabs())
            if lineno == self.errlineno:
                if lexpos:
                    prefixlen = len(prefix) + linenofmtlen + 1
                    print "%s%s"%(" "*(prefixlen + errlinebefore),
                                  "^"*len(self.symbol))
                else:
                    print ""
        if self.parser.parent:
            parent = self.parser.parent
            print "Included from %s"%(parent.filename)
            parent = parent.parent
            while parent:
                print "              %s"%(parent.filename)
        return


class BakeryParser(object):

    def __init__(self, data=None):
        self.lexer = ply.lex.lex(module=self)
        tabmodule = self.__class__.__module__ + "_tab"
        self.yacc = ply.yacc.yacc(module=self, debug=0, write_tables=0)
        if data is not None:
            self.data = data
        else:
            self.data = oebakery.data.BakeryData()
        return


    reserved = {
        'export'	: 'EXPORT',
        'require'	: 'REQUIRE',
        'include'	: 'INCLUDE',
        'inherit'	: 'INHERIT',
        'fakeroot'	: 'FAKEROOT',
        'python'	: 'PYTHON',
        'addtask'	: 'ADDTASK',
        'addhook'	: 'ADDHOOK',
        'def'		: 'DEF',
        'del'		: 'DEL',
        'freeze'	: 'FREEZE',
        'unfreeze'	: 'UNFREEZE',
        }

    tokens = [
        'VARNAME', 'FLAG',
        'ASSIGN', 'EXPASSIGN', 'WEAKASSIGN', 'LAZYASSIGN',
        'APPEND', 'PREPEND', 'POSTDOT', 'PREDOT',
        'STRING',
        'NEWLINE', 'COMMENT',
        ]

    t_ignore = ' \t'


    def t_VARNAME(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_\-\${}/\+\.]*'
        if self.reserved.get(t.value):
            raise ParseError(
                self, "Reserved word not allowed in OE-lite Bakery configuration",
                t, t.value)
        return t

    def t_FLAG(self, t):
        r'\[[a-zA-Z_][a-zA-Z0-9_]*\]'
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


    def t_COMMENT(self, t):
        r'\#[^\n]*'
        pass # no return value, token discarded

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
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
        self.data.set_flag(p[1][0], p[1][1], p[3])
        return

    def p_exp_assignment(self, p):
        '''assignment : varflag EXPASSIGN STRING'''
        print "EXPASSIGN %s"%(p[1][0])
        self.data.set_flag(p[1][0], p[1][1], self.data.expand(p[3], 1))
        return

    def p_defaultval_assignment(self, p):
        '''assignment : variable LAZYASSIGN STRING'''
        self.data.set_flag(p[1][0], "defaultval", p[3])
        return

    def p_weak_assignment(self, p):
        '''assignment : varflag WEAKASSIGN STRING'''
        if self.data.get_flag(p[1][0], p[1][1]) == None:
            self.data.set_flag(p[1][0], p[1][1], p[3])
        return

    def p_append_assignment(self, p):
        '''assignment : varflag APPEND STRING'''
        self.data.append_flag(p[1][0], p[1][1], p[3])
        return

    def p_prepend_assignment(self, p):
        '''assignment : varflag PREPEND STRING'''
        self.data.prepend_flag(p[1][0], p[1][1], p[3])
        return

    def p_predot_assignment(self, p):
        '''assignment : varflag PREDOT STRING'''
        self.data.append_flag(p[1][0], p[1][1], p[3], separator="")
        return

    def p_postdot_assignment(self, p):
        '''assignment : varflag POSTDOT STRING'''
        self.data.prepend_flag(p[1][0], p[1][1], p[3], separator="")
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
        self.data.set_file_mtime(self.filename, mtime)

        self.lexer.lineno = 0
        self.yacc.parse(self.text + '\n', lexer=self.lexer)

        return self.data


#class ParseError(Exception):
#
#    def __init__(self, parser, msg, details=None, symbol=None):
#        self.parser = parser
#        self.msg = msg
#        self.details = details
#        if not symbol and details:
#            self.symbol = details.value
#        else:
#            self.symbol = symbol
#        return
#
#    def __str__(self):
#        return self.msg
#
#    def print_details(self):
#        print self.msg
#        if not self.details:
#            return ""
#        lines = self.parser.text.splitlines()
#        firstline = max(self.details.lineno - 5, 0)
#        lastline = min(self.details.lineno + 5, len(lines) - 1)
#        errlinepos = 0
#        for lineno in xrange(self.details.lineno):
#            errlinepos += len(lines[lineno]) + 1
#        errpos = (self.details.lexpos - 1) - errlinepos
#        errlinebefore = lines[self.details.lineno]\
#            [:(self.details.lexpos - errlinepos)]
#        errlinebefore = len(errlinebefore.expandtabs())
#        linenofmtlen = len(str(lastline))
#        lineprintfmt = "%%s%%%dd %%s"%(linenofmtlen)
#        for lineno in xrange(firstline, lastline):
#            if lineno == self.details.lineno:
#                if lineno:
#                    print ""
#                prefix = "-> "
#            else:
#                prefix = "   "
#            print lineprintfmt%(prefix, lineno + 1,
#                                lines[lineno].expandtabs())
#            if lineno == self.details.lineno:
#                prefixlen = len(prefix) + linenofmtlen + 1
#                print "%s%s"%(" "*(prefixlen + errlinebefore),
#                              "^"*len(self.symbol))
#        return


def parse(path):
    confparser = BakeryParser()
    return confparser.parse(path)


def parse_bakery_conf():
    topdir = oebakery.get_topdir()
    oebakery.chdir(topdir)

    config = parse("conf/bakery.conf")
    if config is None:
        return None

    ok = True

    OEPATH = []
    OERECIPES = []
    PYTHONPATH = []

    OESTACK = config.get("OESTACK") or ""
    gitmodules = oebakery.gitmodules.parse_dot_gitmodules()
    config["__oestack"] = []
    config["__submodules"] = []
    for oestack in OESTACK.split():
        oestack = oestack.split(";")
        path = oestack[0]
        params = {}
        for param in oestack[1:]:
            key, value = param.split("=", 1)
            if key == "remote":
                if not key in params:
                    params[key] = []
                name, url = value.split(",", 1)
                params[key].append((name, url))
            else:
                params[key] = value
        if path.startswith("meta/"):
            if not "oepath" in params:
                params["oepath"] = ""
            if not "pythonpath" in params:
                params["pythonpath"] = "lib"
            if not "oerecipes" in params:
                params["oerecipes"] = "*/*.oe"
        if "srcuri" in params and params["srcuri"].startswith("git://"):
            if not "protocol" in params:
                params["protocol"] = "git"
        if path in gitmodules:
            url = gitmodules[path]['url']
            if "srcuri" in params:
                srcuri_url = "%s%s"%(params["protocol"], params["srcuri"][3:])
                if srcuri_url != url:
                    logger.warning(
                        "mismatch between .gitmodules url and srcuri for %s",
                        path)
            config["__submodules"].append((path, url, params))
        elif "srcuri" in params and params["srcuri"].startswith("git://"):
            url = "%s%s"%(params["protocol"], params["srcuri"][3:])
            config["__submodules"].append((path, url, params))
        config["__oestack"].append((path, params))
        if "oepath" in params:
            if params["oepath"] == "":
                oepath = path
            else:
                oepath = os.path.join(path, params["oepath"])
            OEPATH.append(oepath)
            oerecipes_base = os.path.join(oepath, "recipes")
            if os.path.isdir(oerecipes_base):
                for oerecipes in params["oerecipes"].split(":"):
                    OERECIPES.append(os.path.join(oerecipes_base, oerecipes))
        if "pythonpath" in params:
            if params["pythonpath"] == "":
                PYTHONPATH.append(os.path.abspath(path))
            else:
                pythonpath = os.path.join(path, params["pythonpath"])
                if os.path.exists(pythonpath):
                    PYTHONPATH.append(os.path.abspath(pythonpath))

    OEPATH.insert(0, ".")
    if os.path.isdir("recipes"):
        OERECIPES.insert(0, "recipes/*/*.oe")

    config["OEPATH"] = ":".join(map(os.path.abspath, OEPATH))
    config["OEPATH_PRETTY"] = ":".join(OEPATH)

    config["OERECIPES"] = ":".join(map(os.path.abspath, OERECIPES))
    config["OERECIPES_PRETTY"] = ":".join(OERECIPES)

    config["TOPDIR"] = topdir

    sys.path = PYTHONPATH + sys.path

    logger.debug("OEPATH = %s", config["OEPATH_PRETTY"])
    logger.debug("OERECIPES = %s", config["OERECIPES_PRETTY"])
    logger.debug("PYTHONPATH = %s", PYTHONPATH)

    return config
