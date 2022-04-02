# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   InitParams.py
@Time    :   2023/5/8
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   初始RK,必须要的参数
'''
import os
import sys

load_list = ["LuxScript"]


def load_package(path):
    parent_folder = os.path.dirname(path)
    for dirname in os.listdir(parent_folder):
        if dirname in load_list:
            sys.path.append(os.path.join(parent_folder, dirname))
            load_list.pop(load_list.index(dirname))
        if not load_list:
            return None
    else:
        return load_package(parent_folder)


load_package(os.path.abspath(__file__))

from Lib.Template import TempItem
from Lib.Runner import runner
from Lib.Config import JsonLoadConfig
from Utils.Constant import ErrorCode


class InitLoadConfig(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "init ppu"
        self.expect = "load project info"
        self.tip = "\033[32m{}\033[0m"

    def check_sn(self, sn):
        input_sn = input(self.tip.format("please input sn: "))
        self.assertEqual(ErrorCode.FFFFFFFF, "check init sn", input_sn, sn)

    def exe(self):
        cfg = JsonLoadConfig(cfg_path_name="", cfg_name="jobcontext.json").get_config()
        sn = cfg["unitData"]["name"].strip()
        self.check_sn(sn)


if __name__ == '__main__':
    runner.single_runner(InitLoadConfig)
