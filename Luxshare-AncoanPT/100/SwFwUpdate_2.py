# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   SwFwUpdate_1.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re

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


class SwFwUpdate_2(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "server power"
        self.expect = "server power reset"

    def exe(self):

        data = self.platform.get_platform_data()
        header_bmc_ip = data["ip_address"]

        self.os_run.run(f"ipmitool -I lanplus -H {header_bmc_ip} -U taobao -P 9ijn0okm power reset")

        self.sleep(90)

        if not self.platform.check_uut(action="on"):
            self.fail("header power reset fail")


if __name__ == '__main__':
    runner.single_runner(SwFwUpdate_2)

