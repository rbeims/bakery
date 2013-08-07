import os
import re
import ConfigParser

import oebakery
logger = oebakery.logger


def parse_dot_gitmodules(path='.gitmodules'):
    class gitmodules(file):
        def __init__(self, path):
            return super(gitmodules, self).__init__(path)
        def readline(self):
            line = super(gitmodules, self).readline()
            if line:
                line = line.lstrip()
            return line
    parser = ConfigParser.RawConfigParser()
    if not os.path.exists(path):
        return {}
    parser.readfp(gitmodules(path))
    submodule_re = re.compile('submodule "(.*)"')
    submodules = {}
    for section in parser.sections():
        submodule = submodule_re.match(section)
        if not submodule:
            logger.warning("skipping malformed .gitmodules section: %r",
                           section)
            continue
        submodule = submodule.group(1)
        submodules[submodule] = dict(parser.items(section))
        logger.debug(".gitmodules submodule %s %s",
                     submodule, submodules[submodule])
    return submodules
