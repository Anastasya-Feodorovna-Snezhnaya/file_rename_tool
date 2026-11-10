import logging
from pathlib import Path


def get_logger() -> logging.Logger:
    logger = logging.getLogger("file_rename_tool")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    log_path = Path.cwd() / "rename_tool.log"
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(handler)
    logger.info("日志初始化；当前工作目录：%s", Path.cwd())
    return logger
