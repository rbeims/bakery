from collections import MutableMapping
import oebakery.parse.expandparse

class BaseData(MutableMapping):

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

    def expand(self, val, allow_unexpand=False):
        if not val:
            return val
        expandparser = oebakery.parse.expandparse.ExpandParser(
            self, allow_unexpand)
        expval = expandparser.expand(val)
        return expval


    #def __contains__(self, var):
    #    val = self.getVar(var, 0)
    #    return val is not None
    #
    #def __getitem__(self, var):
    #    return self.getVar(var, 0)
    #    
    #def __setitem__(self, var, val):
    #    self.setVar(var, val)
    #
    #def __delitem__(self, var):
    #    self.delVar(var)
