# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncOamCheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/OAM测试
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


class FuncOamCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "oam function test"
        self.expect = "This is oam function check test on the server"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "UUT.yaml", "name": "oam_conf", "key": "OAM"},
        ]

    def exe(self):
        oam_config = self.config["oam_conf"]

        with self.ssh_connect(uut=self.config["UUT"]):
            for n in oam_config["Num"]:
                parser = self.execute_run(f"ppudbg --device {n}")

                HBM_FS = parser.filter_list(r"(HBM[0-9]{1}-[0-9]+MHZ)")
                for h in HBM_FS:
                    h_l = h.split("-")
                    self.assertEqual(ErrorCode.GPUTFT02, f"oam device {n} {h_l[0]} HBM Frequency", h_l[1],
                                     oam_config['HBM_Frequency'])


if __name__ == '__main__':
    runner.single_runner(FuncOamCheck)
