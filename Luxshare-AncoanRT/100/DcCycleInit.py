# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncCpuCheck.py
@Time    :   2023/5/4
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/CPU测试 （机头）
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


class DcCycleInit(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpu"
        self.expect = "This is cpu function check test on the service"
        self.config = [
            {"file": "BmcDevice.yaml", "name": "bmc_info"},
        ]

    def exe(self):
        self.assertEqual("00000000", "test demo", 2, 2)
        self.platform.put_platform_data(self.config["bmc_info"])


if __name__ == '__main__':
    runner.single_runner(DcCycleInit)
