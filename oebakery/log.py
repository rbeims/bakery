import logging
import sys
import oebakery


class ConsoleFormatter(logging.Formatter):

    def __init__(self):
        super(ConsoleFormatter, self).__init__()
        return

    def format(self, record):
        record.message = record.getMessage()
        fmt = ""
        if not record.levelno == logging.INFO:
            fmt += "%(levelname)s: "
        if record.levelno == logging.DEBUG:
            fmt += "%(name)s: "
        fmt += "%(message)s"
        s = fmt % record.__dict__
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s += "\n\n"
            s = s + record.exc_text + "\n"
        return s

logging.basicConfig(format="%(message)s")

logger = logging.getLogger("bakery")

console_logger = logging.StreamHandler()
console_logger.setLevel(logging.DEBUG)
console_formatter = ConsoleFormatter()
console_logger.setFormatter(console_formatter)

logger.addHandler(console_logger)
logger.propagate = False

def fatal(msg):
    logging.critical("FATAL: %s", msg)
    raise oebakery.FatalError(msg)


# Legacy API (deprecated, for compatibility with old meta-data)

def legacy_warn(msg):
    logging.warning("WARNING: %s", msg)

def legacy_err(msg):
    logging.error("ERROR: %s", msg)

def configure_legacy_logging(debug):
    if debug:
        oebakery.DEBUG = True
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        oebakery.DEBUG = False
        logging.getLogger().setLevel(logging.INFO)
    return

debug = logging.debug
info = logging.info
warn = legacy_warn
err = legacy_err
die = fatal
