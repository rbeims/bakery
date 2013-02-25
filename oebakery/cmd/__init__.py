from __future__ import with_statement # This isn't required in Python 2.6

from cmds import \
    clear, \
    add_builtin_cmds, \
    add_manifest_cmds, \
    cmds_usage, \
    get_cmd, \
    cmd_parser, \
    call

__all__ = [
    "clear",
    "add_builtin_cmds",
    "add_manifest_cmds",
    "cmds_usage",
    "get_cmd",
    "cmd_parser",
    "call",
]

builtin_cmds = [ "init", "clone", "update", "pull" ]
__all__ += builtin_cmds
