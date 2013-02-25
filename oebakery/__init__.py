from __future__ import with_statement # This isn't required in Python 2.6

__version__ = "4"

__all__ = []

import log
from log import logger, fatal
__all__ += [ "log", "logger", "fatal" ]

import cmd
__all__ += [ "cmd" ]


import data
__all__ += [ "data" ]

import parse
__all__ += [ "parse" ]

import path
from path import set_topdir, get_topdir, chdir
__all__ += [ "set_topdir", "get_topdir", "chdir" ]

import shell
from oebakery.shell import call
__all__ += [ "shell", "call" ]


import os
oldpwd = os.getcwd()
__all__ += [ "oldpwd" ]

#
# legacy API - backwards compatibility with OE-lite Bakery 3.x
#

from log import debug, info, warn, err, die

class FatalError(Exception):
    pass

# Logging/output API for manifest commands:
#
# print - for console
#
# import oebakery
#
# oebakery.fatal()
#
# import logging
# logging.debug()
# logging.info()
# logging.warning() - when client/recipe is not responsible for the warning
# logging.error()
#
# import warnings
# warnings.warn() - when client/recipe should be fixed to eliminate the warning
#
# Legacy API (deprecated):
#
# oebakery.debug()
# oebakery.info()
# oebakery.warn()
# oebakery.err()
# oebakery.die()
#
# oebakery.FatalError() - Exception class


#
# New style meta:
#  + has own manifest commands (in lib/oelite/cmd/)
#  + has oelite.baker.add_bake_parser_options(parser) function
#  + has oelite.baker.add_show_parser_options(parser) function
#  + has oelite.baker.OEliteBaker().bake() method
#  + has oelite.baker.OEliteBaker().show() method
#  + configures logging module by itself (to work with bakery 3)
#  + does not use oebakery.DEBUG
#  + does not use oebakery.FatalError()
#  + does not use deprecated oebakery.debug(), oebakery.info() ....
#  + uses logging module
#  + does not use oebakery.die()
#  + uses oebakery.fatal()
#
# Old style meta
#  + does not have own manifest commands (in lib/oelite/cmd/)
#  + has oelite.baker.add_bake_parser_options(parser) function
#  + has oelite.baker.add_show_parser_options(parser) function
#  + has oelite.baker.OEliteBaker().bake() method
#  + has oelite.baker.OEliteBaker().show() method
#  + does normally not use the logging module
#  + uses oebakery.DEBUG
#  + uses oebakery.FatalError()
#  + uses oebakery.debug(), oebakery.info() ....
#  + uses oeabkery.die()
