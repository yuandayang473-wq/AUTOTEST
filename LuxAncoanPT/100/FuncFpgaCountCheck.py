# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   FuncFpgaCountCheck.py
@Time    :   2023/5/23
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/Memory测试  （机头）
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
from Utils.Constant import ErrorCode


class FuncFpgaCountCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Fpga Count"
        self.expect = "This is Fpga Count on the server"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "path", "key": "InitPath"},
        ]

    def exe(self):
        jbog_cfg = self.config["cfg"]["JBOG"]
        fpga_count = jbog_cfg["fpga_count"]

        if fpga_count == "NA":
            

        with self.ssh_connect(uut=self.config["UUT"]):
            parser = self.execute_run(f'lspci -Dnn | grep 0580 | grep -icE "1ded"')
            current_fpga_count = int(parser.get_origin_data())
            self.assertEqual(ErrorCode,"Fpga count", current_fpga_count, int(fpga_count*4))
        


if __name__ == '__main__':
    runner.single_runner(FuncFpgaCountCheck)