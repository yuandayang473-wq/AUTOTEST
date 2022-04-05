# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncFanInfoCheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/PSU测试
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
from Utils.Constant import ErrorCode
from Utils.Utility import multi_column
from Utils.Constant import ErrorCode


class FuncFanInfoCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "fan"
        self.expect = "This is fan info function check test"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": "BMC_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
        ]

    def exe(self):
        server = self.config["cfg"]["SERVER"]
        JBOG = self.config["cfg"]["JBOG"]
        # 获取机头的fan
        with self.action("server Fan"):
            with self.ssh_connect(uut=self.config["UUT"]):
                parser = self.execute_run("ipmitool sdr list |grep -i fan |grep -i RPM")
                # check fan count
                head_fans = multi_column(parser.get_origin_data(), column_index=[0, 2])
                for f_name, status in head_fans:
                    self.assertEqual(ErrorCode.FANTCH01, f"{f_name} status", status, "ok")
                self.assertEqual(ErrorCode.FANTCH02, "server fan count", int(len(head_fans) / 2), server["fan_count"])

        # 获取机尾的fan
        with self.action("JBOG fan"):
            with self.ssh_connect(uut=self.config["JBOG_BMC"]):

                if JBOG["config"] == "W/O scaleout":
                    cmd = "ipmitool sdr list |grep -iE '^fan' |grep -i RPM"
                else:
                    cmd = "ipmitool sdr list |grep -i fan |grep -i RPM"
                parser = self.execute_run(cmd)
                # check fan count
                tail_fans = multi_column(parser.get_origin_data(), column_index=[0, 2])
                for f_name, status in tail_fans:
                    self.assertEqual(ErrorCode.FANTCH01, f"{f_name} status", status, "ok")
                self.assertEqual(ErrorCode.FANTCH02, "jbog fan count", int(len(tail_fans) / 2), JBOG["fan_count"])


if __name__ == '__main__':
    runner.single_runner(FuncFanInfoCheck)
