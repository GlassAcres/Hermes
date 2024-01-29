import logging
from logging.handlers import RotatingFileHandler

class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    green = "\x1b[32;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    COLORS = {
        "DEBUG": grey,
        "INFO": green,
        "WARNING": yellow,
        "ERROR": red,
        "CRITICAL": bold_red
    }

    def __init__(self, fmt="%(levelname)s      %(message)s (%(filename)s:%(lineno)d)"):
        super().__init__(fmt)

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            levelname_color = self.COLORS[levelname] + levelname + self.reset
            record.levelname = levelname_color
        return super(CustomFormatter, self).format(record)

def setup_custom_logger(name, log_file='./utils/logs/app.log'):
    try:
        logger = logging.getLogger(name)
        if not logger.handlers:
            logger.setLevel(logging.INFO)

            # Console Handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(CustomFormatter())
            logger.addHandler(ch)

            # Rotating File Handler
            fh = RotatingFileHandler(log_file, maxBytes=9000000, backupCount=5)
            fh.setLevel(logging.INFO)
            fh.setFormatter(CustomFormatter())
            logger.addHandler(fh)

            logger.propagate = False

        return logger
    except Exception as e:
        print(f"Error setting up logger: {e}")
        raise
