from loguru import logger as _logger
import sys

logger = _logger
logger.remove()
logger.add(sys.stderr, level="INFO")