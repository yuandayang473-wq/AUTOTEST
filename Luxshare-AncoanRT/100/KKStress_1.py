# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   KKStress_2.py
@Time    :   2023/5/9
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   健康检查
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


class KKStress_1(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "kk stress"
        self.expect = "This is kk stress test"

    def enable_ifs(self):
        """
        <Enable IFS>
        ipmitool raw 0x3e 0x5c 0x00 0x01 0x81
        ipmitool raw 0x3e 0x5c 0x37 0x01 0x81

        <Disable IFS (关闭主开关和所有依赖开关)>
        ipmitool raw 0x3e 0x5c 0x00 0x01 0x81
        ipmitool raw 0x3e 0x5c 0x37 0x01 0x80

        <Read IFS Status>
        ipmitool raw 0x3e 0x5f 0x37 0x01
        返回的01 80中, 第二个字节代表状态, 80即0x80即Disabled, 81即0x81即Enable,
        :return:
        """

        parser = self.os_run.run("ipmitool raw 0x3e 0x5f 0x37 0x01", parser_type="raw_parser")
        status = parser.raw_str(1)
        if status == "81":
            self.platform.run(cmd="")
            self.platform.skip_dynamic_tool("not need reboot")
            return

        self.os_run.run("ipmitool raw 0x3e 0x5c 0x00 0x01 0x81")
        self.os_run.run("ipmitool raw 0x3e 0x5c 0x37 0x01 0x81")
        self.platform.run(cmd="reboot")

    def exe(self):
        self.enable_ifs()


if __name__ == '__main__':
    runner.single_runner(KKStress_1)

