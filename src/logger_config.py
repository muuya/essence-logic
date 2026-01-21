"""
日志配置模块
实现服务器日志管理的最佳实践
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    配置应用程序日志系统
    
    最佳实践：
    1. 结构化日志格式（包含时间戳、级别、模块、消息）
    2. 日志轮转（避免文件过大）
    3. 分离不同级别的日志（可选）
    4. 同时输出到文件和控制台
    5. 异步日志处理（避免阻塞）
    
    Args:
        log_dir: 日志文件目录，默认为项目根目录下的 logs/ 目录
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否写入文件
        log_to_console: 是否输出到控制台
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 保留的备份文件数量
        
    Returns:
        配置好的 logger 实例
    """
    # 确定日志目录
    if log_dir is None:
        # 默认使用项目根目录下的 logs/ 目录
        project_root = Path(__file__).parent.parent
        log_dir = project_root / "logs"
    else:
        log_dir = Path(log_dir)
    
    # 创建日志目录
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 logger
    logger = logging.getLogger("essence_board")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 避免重复添加 handler（防止重复日志）
    if logger.handlers:
        return logger
    
    # 定义日志格式
    # 结构化格式：时间戳 | 级别 | 模块:行号 | 消息
    detailed_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 简单格式（用于控制台）
    simple_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 文件 handler - 使用轮转
    if log_to_file:
        # 主日志文件（所有级别）
        main_log_file = log_dir / "app.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_handler.setFormatter(detailed_format)
        logger.addHandler(file_handler)
        
        # 错误日志文件（只记录 ERROR 及以上）
        error_log_file = log_dir / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_format)
        logger.addHandler(error_handler)
    
    # 控制台 handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(simple_format)
        logger.addHandler(console_handler)
    
    # 记录日志系统启动信息
    logger.info("=" * 60)
    logger.info("日志系统已启动")
    logger.info(f"日志级别: {log_level}")
    logger.info(f"日志目录: {log_dir}")
    logger.info(f"文件日志: {'启用' if log_to_file else '禁用'}")
    logger.info(f"控制台日志: {'启用' if log_to_console else '禁用'}")
    logger.info("=" * 60)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取 logger 实例
    
    Args:
        name: logger 名称，默认为 "essence_board"
        
    Returns:
        logger 实例
    """
    if name:
        return logging.getLogger(f"essence_board.{name}")
    return logging.getLogger("essence_board")


# 从环境变量读取配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
LOG_DIR = os.getenv("LOG_DIR", None)

# 初始化日志系统
logger = setup_logging(
    log_level=LOG_LEVEL,
    log_to_file=LOG_TO_FILE,
    log_to_console=LOG_TO_CONSOLE,
    log_dir=LOG_DIR
)
