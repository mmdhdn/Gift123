from loguru import logger
import sys

def get_logger(name: str = "", level: str = "INFO"):
    logger.remove()  # Удаляем стандартный handler
    logger.add(sys.stdout, level=level, format="{time} - {name} - {level} - {message}")
    return logger.bind(name=name)
#
# def get_logger(name: str = "", level: str = "INFO"):
#     return None