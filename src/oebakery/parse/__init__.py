
__all__ = [
    'expandparse', 'confparse', 'bbparse', 'ParseError',
    ]

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
        if self.parser.parent:
            parent = self.parser.parent
            print "Included from %s"%(parent.filename)
            parent = parent.parent
            while parent:
                print "              %s"%(parent.filename)
        return
