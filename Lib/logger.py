#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@ins-ict.com
@Software:   V2
@File    :   Logging.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©ins  2022 . All Rights Reserved.
@Desc    :   None
"""

import logging
import time
import os
import shutil
from colorama import Fore, Style
import re  # 新增导入，用于移除颜色代码

from Lib.Utility import singleton

TMER_FLAG = False
#日志打印等级定义
LOG_DEBUG = logging.DEBUG
LOG_INFO = logging.INFO
LOG_WARN = logging.WARN
LOG_ERROR = logging.ERROR
# 用于测试框架打印的级别，特殊定义为90
LOG_SYS = 90
logging.addLevelName(LOG_SYS, "SYS")
LEVEL_COLOR = {
LOG_DEBUG: Fore.BLUE,
LOG_INFO: Fore.WHITE,
LOG_WARN: Fore.YELLOW,
LOG_ERROR: Fore.RED,
LOG_SYS: Fore.GREEN}

@singleton
class Logger:

    def __init__(self, mode="normal"):
        self.logger = logging.getLogger()
        if mode == "normal":
            self.logger.setLevel(20)
        elif mode == "debug":
            self.logger.setLevel(10)
        else:
            raise Exception("Logger mode set error!")

        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Log")
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        t = time.strftime("%Y%m%d_%H-%M-%S", time.localtime())
        self.log_name = log_path + "\\antotest{}.log".format(t)
        sh = logging.StreamHandler()  # for print out
        fh = logging.FileHandler(self.log_name, encoding="utf-8")  # for file out
        self.logger.addHandler(sh)
        fh.addFilter(self._remove_color_filter())  # 添加过滤器移除颜色代码
        self.logger.addHandler(fh)


    def sys(self, msg, *args, **kwargs):
        t = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        log_msg = '\n'.join(
            [f'{Fore.GREEN}{t}\tSYS\t\t{row}{Style.RESET_ALL}' for row in msg.split('\n')])
        self.logger.log(90, log_msg, *args, **kwargs)
    def debug(self, msg, *args, **kwargs):
        t = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        log_msg = '\n'.join(
            [f'{Fore.BLUE}{t}\tDEBUG\t{row}{Style.RESET_ALL}' for row in msg.split('\n')])
        self.logger.debug(log_msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        t = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        log_msg = '\n'.join(
            [f'{Fore.WHITE}{t}\tINFO\t{row}{Style.RESET_ALL}' for row in msg.split('\n')])
        self.logger.info(log_msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        t = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        log_msg = '\n'.join(
            [f'{Fore.YELLOW}{t}\tWARNING\t{row}{Style.RESET_ALL}' for row in msg.split('\n')])
        self.logger.warning(log_msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        t = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        log_msg = '\n'.join(
            [f'{Fore.RED}{t}\tERROR\t{row}{Style.RESET_ALL}' for row in msg.split('\n')])
        self.logger.error(log_msg, *args, **kwargs)

    def _remove_color_filter(self):
        """创建一个过滤器，用于移除颜色代码"""
        class RemoveColorFilter(logging.Filter):
            def filter(self, record):
                record.msg = re.sub(r'\x1b\[[0-9;]*m', '', record.msg)  # 移除ANSI颜色代码
                return True
        return RemoveColorFilter()




if __name__ == '__main__':
    logger = Logger()
    logger.info("this is info")
    logger.debug("this is debug")
    logger.sys("this is sys")
    logger.warning("this is warning")
    logger.error("this is error")