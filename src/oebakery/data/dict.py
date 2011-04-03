import oebakery.parse.expandparse

class DictData:

    def __init__(self):
        self.dict = {}
        return

    def createCopy(self):
        import copy
        return copy.copy(self)

    def getVarFlag(self, var, flag):
        try:
            return self.dict[var][flag]
        except KeyError:
            return None

    def setVarFlag(self, var, flag, value):
        #print "setVarFlag %s %s %s"%(var, flag, repr(value))
        if not var in self.dict:
            self.dict[var] = {}
        self.dict[var][flag] = value
        return

    def appendVarFlag(self, var, flag, value):
        current = self.getVarFlag(var, flag)
        if current == None:
            self.setVarFlag(var, flag, value)
        else:
            self.setVarFlag(var, flag, current + value)

    def prependVarFlag(self, var, flag, value):
        current = self.getVarFlag(var, flag)
        if current == None:
            self.setVarFlag(var, flag, value)
        else:
            self.setVarFlag(var, flag, value + current)

    def delVarFlag(self, var, flag):
        try:
            del self.dict[var][flag]
        except KeyError:
            pass
        return

    def getVar(self, var, expand=2):
        val = self.getVarFlag(var, "val")
        if expand and val:
            val = self.expand(val, expand == 1)
        return val

    def setVar(self, var, value, expand=0):
        return self.setVarFlag(var, "val", value)

    def appendVar(self, var, value):
        return self.appendVarFlag(var, "val", value)

    def prependVar(self, var, value):
        return self.prependVarFlag(var, "val", value)

    def delVar(self, var):
        try:
            del self.dict[var]
        except KeyError:
            pass
        return

    def expand(self, val, allow_unexpand=False):
        if not val:
            return val
        expandparser = oebakery.parse.expandparse.ExpandParser(self, allow_unexpand)
        expval = expandparser.expand(val)
        return expval


    def __str__(self):
        return repr(self.dict)

    def __iter__(self):
        return self.dict.__iter__

    def __len__(self):
        return len(self.dict.keys())

    def __contains__(self, var):
        val = self.getVar(var, 0)
        return val is not None

    def __getitem__(self, var):
        val = self.getVar(var, 0)
        if val is None:
            raise KeyError(var)
        else:
            return val

    def __setitem__(self, var, val):
        self.setVar(var, val)

    def __delitem__(self, var):
        self.delVar(var)
