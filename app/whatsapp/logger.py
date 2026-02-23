import logging
from app.core.config import settings

# Setting up structured logging
logger = logging.getLogger("whatsapp_layer")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": %(message)s}'
)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
