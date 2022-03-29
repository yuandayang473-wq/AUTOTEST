# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncSensorCheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/Sensor测试/sensor检查
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


class FuncSensorCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "uart"
        self.expect = "This is uart function check test"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": "BMC_01"},
        ]

    def exe(self):
        # 获取机头的sdr
        with self.ssh_connect(uut=self.config["UUT"]):
            self.execute_run("ipmitool sdr")

        # 获取机尾的sdr
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            self.execute_run("ipmitool sdr")


if __name__ == '__main__':
    runner.single_runner(FuncSensorCheck)

