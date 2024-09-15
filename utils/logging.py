from logging import DEBUG, getLogger, StreamHandler, Formatter, FileHandler, Logger
from datetime import datetime
import os

class LoggerConfig:
    def __init__(self, logs_directory: str = 'logs', name: str = ''):
        """
        Initializes the logging configurations.

        Args:
            logs_directory (str, optional): Directory to save logs to. Defaults to 'logs'.
            name (str, optional): Name of current logging handler. Defaults to ''.
        """
        self.logs_directory = logs_directory
        self.name = name
        self.logger = getLogger(name=name)
        self.logger.setLevel(DEBUG)
        self.logger.propagate = False

        # Ensure log directory exists
        os.makedirs(self.logs_directory, exist_ok=True)

        # Log filename based on current date
        log_name = os.path.join(self.logs_directory, f"{datetime.now().strftime('%y%m%d')}.log")

        # File and Console Handlers
        self.filelogger = FileHandler(filename=log_name, encoding='utf8')
        self.filelogger.setLevel(DEBUG)

        self.consolelogger = StreamHandler()
        self.consolelogger.setLevel(DEBUG)

        # Set formatters
        self.set_formatters()

        # Add handlers
        self.logger.addHandler(self.filelogger)
        self.logger.addHandler(self.consolelogger)

    def set_formatters(self):
        """
        Sets the log format for both file and console handlers.
        """
        if self.name:
            formatter = Formatter('[%(levelname)s %(filename)s:%(lineno)s - %(funcName)s ][ %(name)s ] %(asctime)s %(message)s')
        else:
            formatter = Formatter('[%(levelname)s %(filename)s:%(lineno)s - %(funcName)s ] %(asctime)s %(message)s')

        self.consolelogger.setFormatter(formatter)
        self.filelogger.setFormatter(formatter)

    def get_logger(self) -> Logger:
        """
        Returns the configured logger instance.

        Returns:
            Logger: Logging instance.
        """
        return self.logger
