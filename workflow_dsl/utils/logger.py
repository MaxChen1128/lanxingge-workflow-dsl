"""日志工具。"""

import logging


def get_logger(name: str) -> logging.Logger:
    """获取统一前缀的日志器。"""
    logger = logging.getLogger(f"lanxingge.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
