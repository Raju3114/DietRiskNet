import os
import logging
from logging.handlers import RotatingFileHandler

# Create logs directory
LOGS_DIR = os.getenv("LOGS_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs")))
os.makedirs(LOGS_DIR, exist_ok=True)

# Central formatter
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s"
)

def setup_logger(name: str, log_filename: str, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if setup multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        file_path = os.path.join(LOGS_DIR, log_filename)
        file_handler = RotatingFileHandler(file_path, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

# Individual Loggers
app_logger = setup_logger("app", "application.log")
api_logger = setup_logger("api", "api.log")
auth_logger = setup_logger("auth", "auth.log")
db_logger = setup_logger("db", "database.log")
ml_logger = setup_logger("ml_inference", "inference.log")
