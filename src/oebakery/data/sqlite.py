import os
from pysqlite2 import dbapi2 as sqlite
import oebakery.parse.expandparse
from oebakery.data.base import BaseData

class SqliteData(BaseData):

    def __init__(self, dbfile=":memory:", dump=None):
        self.db = sqlite.connect(dbfile)
        self.db.text_factory = str
        if not self.db:
            raise Exception("could not create in-memory sqlite db")
        self.dbfile = dbfile
        if dump:
            self.db.executescript(dump)
        else:
            self.create_tables()
        return


    def createCopy(self, dbfile=":memory:"):
        dump = self.full_dump()
        return SqliteData(dbfile=dbfile, dump=dump)



    def __repr__(self):
        return 'SqliteData(%s)'%(repr(self.dbfile))


    def __str__(self):
        return self.full_dump()


    def __eq__(self):
        raise Exception("SqliteData.__eq__() not implemented")
        return False


    def __hash__(self):
        raise Exception("SqliteData.__hash__() not implemented")
        return


    def __nonzero__(self):
        raise Exception("SqliteData.__nonzero__() not implemented")
        return True


    def __len__(self): # required by Sized
        raise Exception("SqliteData.__len__() not implemented")


    def __getitem__(self, key): # required by Mapping
        return self.getVar(key)


    def __setitem__(self, key, value): # required by MutableMapping
        self.setVar(key, value)
        return value


    def __delitem__(self, key): # required by MutableMapping
        raise Exception("SqliteData.__del__() not implemented")


    def __iter__(self): # required by Iterable
        raise Exception("SqliteData.__iter__() not implemented")


    def __reversed__(self):
        raise Exception("SqliteData.__reversed__() not implemented")


    def __contains__(self, item): # required by Container
        val = self.getVar(item)
        return val is not None


    def keys(self):
        return flatten_single_column_rows(self.db.execute(
            "SELECT var FROM varflag WHERE flag=''",
            locals()))


    def create_tables(self):
        c = self.db.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS varflag ( "
                  "var TEXT, "
                  "flag TEXT, "
                  "val TEXT, "
                  "UNIQUE (var, flag) ON CONFLICT REPLACE )")

        c.execute("CREATE TABLE IF NOT EXISTS files ( "
                  "fn TEXT PRIMARY KEY ON CONFLICT REPLACE, "
                  "mtime TEXT  )")

        return


    def full_dump(self):
        return os.linesep.join([line for line in self.db.iterdump()])


    def setVarFlag(self, var, flag, val):
        #print "setVarFlag(%s, %s, %s)"%(var, flag, repr(val))
        self.db.execute(
            "INSERT INTO varflag (var, flag, val) VALUES (:var, :flag, :val)",
            locals())
        return


    def setVar(self, var, val):
        #print "setVar var=%s val=%s"%(repr(var), repr(val))
        self.db.execute(
            "INSERT INTO varflag (var, flag, val) VALUES (:var, '', :val)",
            locals())
        return


    def getVarFlag(self, var, flag, expand=1):
        val = flatten_single_value(self.db.execute(
            "SELECT val FROM varflag WHERE var=:var AND flag=:flag",
            locals()))
        if expand and val:
            val = self.expand(val, expand == 2)
        return val


    def getVar(self, var, expand=1):
        val = flatten_single_value(self.db.execute(
            "SELECT val FROM varflag WHERE var=:var AND flag=''",
            locals()))
        if expand and val:
            val = self.expand(val, expand == 2)
        return val


    def setFileMtime(self, fn, mtime):
        self.db.execute(
            "INSERT INTO files (fn, mtime) VALUES (:fn, :mtime)",
            locals())
        return


    def getFileMtime(self, fn):
        return flatten_single_value(self.db.execute(
            "SELECT mtime FROM files WHERE fn=:fn",
            locals()))


    def dict(self):
        varflags = self.db.execute(
            "SELECT var,flag,val FROM varflag",
            locals())
        d = {}
        for (var, flag, val) in varflags:
            if not var in d:
                d[var] = {}
            d[var][flag] = val
        return d


def flatten_single_value(rows):
    row = rows.fetchone()
    if row is None:
        return None
    return row[0]


def flatten_one_string_row(rows):
    row = rows.fetchone()
    if row is None:
        return None
    return str(row[0])


def flatten_single_column_rows(rows):
    rows = rows.fetchall()
    if not rows:
        return []
    for i in range(len(rows)):
        rows[i] = rows[i][0]
    return rows


def var_to_tuple(v):
    return (v,)

def tuple_to_var(t):
    return t[0]
