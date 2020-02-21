#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/17 15:18
# @Author  : lichenxiao

import time
import logging
import os


def create_logger(loggername='logger', levelname='DEBUG'):
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    logger = logging.getLogger(loggername)
    logger.setLevel(levels[levelname])

    datefmt = '%Y-%m-%d-%H:%M:%S'
    logger_format = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(filename)s][%(funcName)s][%(lineno)03s]: %(message)s", datefmt)
    console_format = logging.Formatter("[%(levelname)s][%(filename)s][%(lineno)03s] %(message)s", datefmt)

    handler_console = logging.StreamHandler()
    handler_console.setFormatter(console_format)
    handler_console.setLevel(logging.INFO)

    path = './logs'  # 日志目录
    if not os.path.isdir(path):
        os.mkdir(path)
    today = time.strftime("%Y-%m-%d")  # 日志文件名
    common_filename = path + '/%s.log' % today
    handler_common = logging.FileHandler(common_filename, mode='a+', encoding='utf-8')
    handler_common.setLevel(levels[levelname])
    handler_common.setFormatter(logger_format)

    logger.addHandler(handler_console)
    logger.addHandler(handler_common)

    return logger


logger = create_logger('qimai')
