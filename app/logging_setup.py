import logging

from app.config import BASE_DIR

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler(BASE_DIR / "bot.log")],
)
logger = logging.getLogger(__name__)
