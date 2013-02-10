import re
import types


NO_EXPANSION      = 0
FULL_EXPANSION    = 1


class ExpansionStack:

    def __init__(self):
        self.stack = []
        self.python = False
        return

    def push(self, var):
        if var in self.stack:
            raise Exception("Circular expansion: %s"%("->".join(self.stack)))
        self.stack.append(var)
        return

    def pop(self):
        del self.stack[-1:]
        return

    def __len__(self):
        return len(self.stack)

    def __str__(self, prefix="  "):
        return prefix + ("\n%s"%(prefix)).join(self.stack)


class BakeryData:

    def __init__(self):
        self._dict = {}
        self.mtime = {}
        self.expand_stack = ExpansionStack()
        return

    def dict(self):
        return self._dict

    def set(self, var, value):
        return self.set_flag(var, "", value)

    def get(self, var, expand=FULL_EXPANSION):
        return self._get(var, expand)[0]

    def _get(self, var, expand=FULL_EXPANSION):
        #print "_get var=%s expand=%s"%(var, expand)
        assert isinstance(expand, int)
        try:
            val = self._dict[var][""]
        except KeyError:
            try:
                val = self._dict[var]["defaultval"]
            except KeyError:
                val = None
        if not expand:
            return (val, None)
        if not var in self._dict:
            return (None, None)
        if not isinstance(val, (basestring, types.NoneType)):
            return (val, None)

        deps = set()
        #print "get expanding %s=%s"%(var, repr(val))
        expand_method = self.get_flag(var, "expand")
        if expand_method:
            expand_method = int(expand_method)
        else:
            expand_method = expand
        if expand_method != NO_EXPANSION and val:
            self.expand_stack.push("${%s}"%var)
            (val, deps) = self._expand(val, expand_method)
            self.expand_stack.pop()

        return (val, deps)

    def set_flag(self, var, flag, value):
        if not var in self._dict:
            self._dict[var] = {}
        self._dict[var][flag] = value
        return

    def get_flag(self, var, flag):
        try:
            return self._dict[var][flag]
        except KeyError:
            return None

    def del_var(self, var):
        try:
            del self._dict[var]
        except KeyError:
            pass
        return

    def del_flag(self, var, flag):
        try:
            del self._dict[var][flag]
        except KeyError:
            pass
        return

    #def append(self, var, value, separator=" "):
    #    print "append var=%s value=%s seperator=%s"%(var, value, separator)
    #    current = self.get(var)
    #    if current == None:
    #        self.set(var, value)
    #    else:
    #        self.set(var, current + separator + value)

    def append_flag(self, var, flag, value, separator=" "):
        current = self.get_flag(var, flag)
        if current == None:
            self.set_flag(var, flag, value)
        else:
            self.set_flag(var, flag, current + separator + value)


    #def prepend(self, var, value, separator=" "):
    #    current = self.get(var)
    #    if current == None:
    #        self.set(var, value)
    #    else:
    #        self.set(var, value + separator + current)

    def prepend_flag(self, var, flag, value, separator=" "):
        current = self.get_flag(var, flag)
        if current == None:
            self.set_flag(var, flag, value)
        else:
            self.set_flag(var, flag, value + separator + current)


    #def set_file_mtime(self, filename, path, mtime):
    def set_file_mtime(self, filename, mtime):
        self.mtime[filename] = mtime

    def get_file_mtime(self, filename):
        if not filename in self.mtime:
            return None
        return self.mtime[filename]


    def __repr__(self):
        return '%s()'%(self.__class__.__name__)

    def __str__(self):
        return repr(self._dict)

    def __eq__(self):
        raise Exception("BakeryData.__eq__() not implemented")

    def __hash__(self):
        raise Exception("BakeryData.__hash__() not implemented")

    def __nonzero__(self):
        return len(self._dict) > 0

    def __len__(self): # required by Sized
        return len(self._dict)

    def __getitem__(self, key): # required by Mapping
        return self.get(key, 0)

    def __setitem__(self, key, value): # required by MutableMapping
        self.set(key, value)
        return value

    def __delitem__(self, key): # required by MutableMapping
        self.del_var(key)
        return

    def __iter__(self):
        return self._dict.__iter__

    def __reversed__(self):
        raise Exception("BakeryData.__reversed__() not implemented")

    def __contains__(self, item):
        val = self.get(item, 0)
        return val is not None


    def expand(self, string, method=FULL_EXPANSION):
        """Expand string using variable data.

        Arguments:
        string -- String to expand
        method -- Expansion method (default: FULL_EXPANSION)

        Expansion methods:
        NO_EXPANSION -- no recursive expansion
        FULL_EXPANSION -- full expansion, all variables must be expanded
        """
        #print "expand method=%s string=%s"%(method, repr(string))
        (new_string, deps) = self._expand(string, method)
        return new_string

    def _expand(self, string, method):
        #print "_expand method=%s string=%s"%(method, repr(string))
        orig_string = string
        var_re    = re.compile(r"\${[^@{}]+}")
        python_re = re.compile(r"\${@.+?}")
        deps = set()
        expanded_string = ""
        string_ptr = 0
        for var_match in var_re.finditer(string):
            var = var_match.group(0)[2:-1]
            (val, recdeps) = self._get(var)
            if val is None:
                if method == FULL_EXPANSION:
                    raise Exception("Cannot expand variable ${%s}"%(var),
                                    self.expand_stack)
            expanded_string += (string[string_ptr:var_match.start(0)] +
                                "%s"%(val,))
            string_ptr = var_match.end(0)
            deps.add(var)
            if recdeps:
                deps.union(recdeps)
        expanded_string += string[string_ptr:]
        #print "returning expanded string %s"%(repr(expanded_string))
        return (expanded_string, deps)
