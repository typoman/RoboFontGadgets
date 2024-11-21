import logging
import sys
from fontgadgets import getEnvironment

logging.addLevelName(logging.ERROR, '| FAILED ')
logging.addLevelName(logging.WARNING, '| WARNING ')
logging.addLevelName(logging.INFO, '')
logging.addLevelName(logging.DEBUG, '')


class LogFormatter(logging.Formatter):
	COLORS = {
			logging.WARNING: '1;30;44',
			logging.ERROR: '1;30;41',
			logging.DEBUG: '0;30;46',
			logging.INFO: '0;30;42',
			}

	COLOR_SEQ = "\x1b[1;%sm"

	def format(self, record):
		levelno = record.levelno
		color = self.COLOR_SEQ % self.COLORS[levelno]
		record.module = color + " " + record.module.upper()
		record.levelname = color + record.levelname + "\x1b[0m "
		return logging.Formatter.format(self, record)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
if getEnvironment() == 'Shell': # RF doesn show colors in the output
	formatter = LogFormatter('%(module)s %(levelname) s%(message)s')
	handler.setFormatter(formatter)
logger.addHandler(handler)
