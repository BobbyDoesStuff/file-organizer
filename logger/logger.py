from loguru import logger
import sys

class LoggerManager:
	def __init__(self):
		self._setup()

	def _setup(self):
		# Configuration for console logging
		log_format="<cyan>{time:YYYY-MM-DD HH:mm:ss zz}</cyan> " \
            "|<level>{level}</level>| <yellow>Line{line: >4} " \
            "({file}):</yellow> <level>{message}</level> "
		logger.remove()  # Remove all existing handlers
		logger.add(
			sys.stdout,
			level="INFO",
        	format=log_format
		)

		# Configuration for file logging
		logger.add(
			"logs/{time:YYYY-MM-DD}.log",
			#retention="True"
			rotation="1 day",
			compression="zip",
			level="ERROR"
		)

	def get_logger(self):
		return logger

# Create a default logger instance so it's ready to use
default_logger = LoggerManager().get_logger()
