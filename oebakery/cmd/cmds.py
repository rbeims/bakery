import optparse
import os


import oebakery
logger = oebakery.logger


__cmds = {}


def get_cmd(name):
    __cmds
    if not name in __cmds:
        return None
    return __cmds[name]


def clear():
    __cmds = {}


def add_cmd(module, cmd_name, cmd_type):
    logger.debug("adding %s command: %s", cmd_type, cmd_name)
    cmd = __import__("%s.%s"%(module, cmd_name.replace("-", "_")),
                     globals(), locals(),
                     ["run", "description", "arguments"], -1)
    cmd.name = cmd_name
    if not "flags" in dir(cmd):
        cmd.flags = ()
    __cmds[cmd_name] = cmd
    return


def add_builtin_cmds():
    for cmd_name in oebakery.cmd.builtin_cmds:
        add_cmd("oebakery.cmd", cmd_name, "builtin")
    return



def clean_orphaned_pycs(directory):
    """Remove all .pyc files without a correspondent module"""
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".pyc"):
                pyc = os.path.join(root, f)
                if not os.path.exists(pyc[:-1]):
                    logger.debug("deleting orphaned file %s" % pyc)
                    os.unlink(pyc)
    return


def add_manifest_cmds():
    logger.debug("add_manifest_cmds()")
    try:
        import oelite
        clean_orphaned_pycs(os.path.join(oelite.__path__[0], "cmd"))
        import oelite.cmd
        module = "oelite.cmd"
        cmds = oelite.cmd.manifest_cmds
        cmd_type = "manifest"
    except ImportError, e:
        logger.debug("import oelite.cmd failed", exc_info=True)
        try:
            import oelite.baker
        except:
            return False
        module = "oebakery.cmd"
        cmds = ("bake", "show")
        cmd_type = "legacy manifest"
    for cmd_name in cmds:
        add_cmd(module, cmd_name, cmd_type)
    return True


def cmds_usage():
    usage = "Commands:"
    for cmd_name in sorted(__cmds.keys()):
        cmd = __cmds[cmd_name]
        usage += "\n  %-21s "%(cmd_name)
        if "description" in dir(cmd) and cmd.description:
            if isinstance(cmd.description, basestring):
                usage += cmd.description
            else:
                usage += cmd.description[0]
        else:
            usage += "TBD"
    return usage


def cmd_parser(cmd):
    try:
        description = cmd.description
        if description and not isinstance(description, basestring):
            description = "\n".join(description)
            # FIXME: use something like format_textblock to format to console
            # width and handle the 2-space indentation here instead of
            # requiring command writers to bother about it.
    except AttributeError, e:
        description = ""
    try:
        arguments = ""
        if cmd.arguments:
            description += "\n\nArguments:"
            for (arg_name, arg_descr, arg_opt) in cmd.arguments:
                if arg_opt == 0:
                    arguments += " <%s>"%(arg_name)
                elif arg_opt == 1:
                    arguments += " [%s]"%(arg_name)
                elif arg_opt == 2:
                    arguments += " [%s]*"%(arg_name)
                else:
                    arguments += " ?%s?*"%(arg_name)
                description += "\n  %-21s %s"%(arg_name, arg_descr)
    except AttributeError, e:
        arguments = ""
    parser = optparse.OptionParser("""
  %%prog %s [options]%s

  %s."""%(cmd.name, arguments, description))
    ret = call(cmd, "add_parser_options", parser)
    if ret is not None and ret!= 0:
        logger.error("%s.add_parser_options failed: %r", cmd.name, ret)
        return None
    return parser


def call(cmd, function, *args):
    if not function in dir(cmd):
        return None
    logger.debug("%s.%s()", cmd.name, function)
    function = eval("cmd.%s"%(function))

    try:
        ret = function(*args)
    except Exception, e:
        if hasattr(e, "print_details"):
            e.print_details()
        logger.exception("exception in %s.%s()", cmd.name, function.__name__)
        return "Exception: %s"%(e)

    if not ret:
        return 0
    if isinstance(ret, int):
        return "error: %d"%(ret)
    return ret
