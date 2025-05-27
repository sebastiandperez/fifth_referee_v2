import logging
import os

class BaseLoader:
    """
    Base loader class to handle database connection and logging for all entity loaders.
    """
    def __init__(self, conn, log_name="loader"):
        self.conn = conn
        self.logger = self._setup_logger(log_name)

    def _setup_logger(self, log_name):
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, f"{log_name}.log")
        logger = logging.getLogger(log_name)
        if not logger.hasHandlers():
            handler = logging.FileHandler(log_path)
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def log_info(self, message):
        print(message)  # Still print to console
        self.logger.info(message)

    def log_error(self, message):
        print(message)
        self.logger.error(message)
