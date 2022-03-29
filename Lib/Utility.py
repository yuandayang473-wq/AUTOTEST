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

import time


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


def get_file_content(file):
    data = ""
    with open(file, "r", encoding="utf-8", errors='ignore') as f:
        while True:
            d = f.read(1024)
            if not d:
                break
            data += d
    return data


if __name__ == '__main__':
    pass
