#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   Logging.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
"""

import logging
import time
import os
import shutil

from .Error import FormatError


def get_file_name(file_path):
    """[summary]

    Args:
        file_path ([str]): [file name abcpath]

    Raises:
        TypeError: [not string]
        FormatError: [endswith not .py]

    Returns:
        [str]: [generate a name]
    """
    # check file name is str
    if not isinstance(file_path, str):
        raise TypeError("file name is string")
    # check file name format
    if not file_path.endswith(".py"):
        raise FormatError("file name must be .py")
    file_name = os.path.basename(file_path)
    new_name = file_name.replace(".py", "")
    return new_name


class LogPath(object):
    def __init__(self, case_name, folder=None, sub_folder=None):
        # def __init__(self, case_name, folder=None):
        if folder is None or folder == '':
            if sub_folder:
                self.__dir = os.path.join(self.find_root(__file__), "Log", sub_folder)
            else:
                self.__dir = os.path.join(self.find_root(__file__), "Log")
            # self.__dir = os.path.join(self.find_root(__file__), "Log")
        else:
            self.__dir = folder
        self.case_name = case_name

    def find_root(self, abspath_):
        file_name = os.path.basename(abspath_)
        folder = os.path.dirname(abspath_)
        if file_name == "Lib":
            return folder
        else:
            return self.find_root(folder)

    @property
    def logfile(self):
        return self.__dir

    def get_log_folder(self):
        return self.__dir

    def path_gen(self):
        log_dir = self.__dir
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        return log_dir

    def log_name(self):
        log_dir = self.path_gen()
        time_tag = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
        # case_name = get_file_name(sys.argv[0])

        # log_name = os.path.join(log_dir, "%s.log" % (str(case_name) + '-' + time_tag))
        log_name = os.path.join(log_dir, "%s.log" % (str(self.case_name) + '-' + time_tag))
        return log_name


class CaseLogger:

    def __init__(self, case_logger, log_name, prefix_format=None, mode="debug"):
        # self.logger = self.ROOT_LOGGER.getChild(case)
        self.log_name = log_name
        self.logger = case_logger
        self.logger.setLevel(logging.DEBUG)

        if prefix_format:
            fmt = logging.Formatter(f'[{prefix_format}]---[%(asctime)s] [%(levelname)s] %(message)s',
                                    '%Y-%m-%d %H:%M:%S')
        else:
            fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

        fh = logging.FileHandler(log_name, encoding="UTF-8")  # for file out
        fh.setFormatter(fmt)
        self.logger.addHandler(fh)
        sh = logging.StreamHandler()  # for print out
        sh.setFormatter(fmt)
        self.logger.addHandler(sh)

        if mode == "normal":
            sh.setLevel(30)  # change print out level
            fh.setLevel(10)  # change file out level:debug:10

        elif mode == "debug":
            sh.setLevel(10)  # change print out level
            fh.setLevel(10)  # change file out level:debug:10

    def debug(self, msg, *args, **kwargs):
        self.logger.name = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.name = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.name = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.name = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.name = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        self.logger.critical(msg, *args, **kwargs)

    def get_name(self):
        return self.log_name


class RootLogger(object):
    LOG_ROOT_PATH = None
    ROOT_LOGGER = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RootLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, folder=None, sub_folder=None):
        if not self.ROOT_LOGGER:
            root_logger_name = self.generate_log_folder(folder, sub_folder)
            self.ROOT_LOGGER = logging.getLogger(root_logger_name)

    def update_root_logger(self, folder, sub_folder):
        del self.ROOT_LOGGER
        del self.LOG_ROOT_PATH
        root_logger_name = self.generate_log_folder(folder, sub_folder)
        self.ROOT_LOGGER = logging.getLogger(root_logger_name)

    def case_logger(self, case, prefix_format=None, log_flag="debug"):
        case_logger = self.ROOT_LOGGER.getChild(case)
        # time_tag = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
        # log_name = os.path.join(self.ROOT_LOGGER.name, "%s.log" % (case + '-' + time_tag))
        log_name = os.path.join(self.ROOT_LOGGER.name, f"{case}.log")
        return CaseLogger(case_logger, log_name, prefix_format, log_flag)

    def generate_log_folder(self, folder, sub_folder):
        """
        创建log 文件夹
        :param folder: 文件夹名字
        :param sub_folder: 子文件夹名称
        :return:
        """
        log_parent = self.find_log_folder_prefix(__file__)
        if not self.LOG_ROOT_PATH:
            if folder is None or folder == '':
                folder = "Log"

            if sub_folder is None or folder == '':
                folder = os.path.join(log_parent, folder)
            else:
                folder = os.path.join(log_parent, folder, sub_folder)

            self.LOG_ROOT_PATH = folder

        if os.path.isdir(self.LOG_ROOT_PATH):
            shutil.rmtree(self.LOG_ROOT_PATH, ignore_errors=True)
        os.makedirs(self.LOG_ROOT_PATH)

        return folder

    def find_log_folder_prefix(self, abspath_):
        """
        查找当前log 的文件夹前缀
        :param abspath_: 当前文件的绝对路径
        :return: 上一级绝对的路径的 Log文件夹的路径
        """
        file_name = os.path.basename(abspath_)
        folder = os.path.dirname(abspath_)
        if file_name == "Lib":
            return folder
        else:
            return self.find_log_folder_prefix(folder)


class LoggerFactory:

    @staticmethod
    def generate_logger(folder=None, sub_folder=None):
        return RootLogger(folder, sub_folder)
