#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   Utility.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
"""

import os
import time
from optparse import OptionParser
from selenium import webdriver

from .Config import YamlLoadConfig
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


def set_options(extend_para=[]):
    optparser = OptionParser()
    if extend_para:
        for p_file, p_dict in extend_para:
            c = YamlLoadConfig(cfg_name=p_file)
            i_p = p_dict.get("include", [])
            e_p = p_dict.get("exclude", [])
            default_p = p_dict.get("default", {})

            if not i_p:
                params = c.get_config()
                i_p = params.keys()

            p_list = set(i_p) - set(e_p)

            for section in p_list:
                para = c.data(section)
                if section in default_p:
                    para["default"] = default_p[section]
                optparser.add_option('--' + str(section), **para)
    else:
        cnf = YamlLoadConfig(cfg_name="Param.yaml")
        common_para = cnf.get_config()
        for section, value in common_para.items():
            optparser.add_option('--' + str(section), **value)
    options, args = optparser.parse_args()
    return options, optparser


def gen_firefox_profile(downloadDir):
    fp = webdriver.FirefoxProfile()
    fp.set_preference("browser.download.folderList", 2)
    fp.set_preference("browser.download.manager.showWhenStarting", False)
    fp.set_preference("browser.download.dir", downloadDir)
    fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
    return fp


class SleepTime:
    _instance = None

    def __new__(cls, *args, **kwargs):

        if cls._instance:  # If there is already a singleton, do not grab the lock, to avoid IO wait
            return cls._instance

        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.logger = None

    def __call__(self, sec):
        self.set_sleep_sec(sec)

    def set_logger(self, logger):
        self.logger = logger

    def _logger_info(self, sec):
        self.logger.info(f"delay time: {sec} second")

    def set_sleep_sec(self, sec):
        self._logger_info(sec)
        time.sleep(sec)


class Step:
    _instance = None

    def __new__(cls, *args, **kwargs):

        if cls._instance:  # If there is already a singleton, do not grab the lock, to avoid IO wait
            return cls._instance

        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._logger = None

    def __call__(self, num=None, desc=None):
        if num is None and desc is not None:
            self._logger.info(f"{desc}".center(80, "="))
        else:
            self.step_num = num
            if num >= 2:
                self.log_step_result(num - 1)
            self._logger.info(f"step_{num}: {desc}".center(80, "="))

    def set_logger(self, logger):
        self._logger = logger

    def log_step_result(self, step_num, res="PASS"):
        if not hasattr(self, "step_num"):
            return None
        if res == "PASS":
            self._logger.info(f"step_{step_num}: {res}".center(80, "="))
        else:
            self._logger.error(f"step_{step_num}: {res}".center(80, "="))

    def callback(self):
        pass


if __name__ == '__main__':
    pass
