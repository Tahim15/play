import os
import logging
from logging.handlers import RotatingFileHandler

API_ID = int(os.environ.get("API_ID", "16531092"))
API_HASH = os.environ.get("API_HASH", "b073b97bd4c8c56616fc2cbbd4da845a")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7524524705:AAH7aBrV5cAZNRFIx3ZZhO72kbi4tjNd8lI")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002398179296"))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 30))  # Check every 5 minutes
CAPTCHA_API_KEY = os.environ.get("CAPTCHA_API_KEY", "42341e63a823ae375e6bef411db7ce85")

PORT = os.environ.get("PORT", "8087")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
  
