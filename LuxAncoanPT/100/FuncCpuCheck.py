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
from Utils.Constant import ErrorCode
from Utils.Init import load_mes_info


class FuncCpuCheck(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "cpu"
        self.expect = "This is cpu function check test on the service"
        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.mes_info["info"]["rk"]},
        ]

    def exe(self):
        server = self.config["cfg"]["SERVER"]
        e_model_name = server["cpu_type"]
        e_socket_count = server["cpu_count"]
        with self.ssh_connect(uut=self.config["UUT"]):
            self.step(1, "get lscpu info")
            parser = self.execute_run("lscpu")

            self.step(2, "check cpu info")
            # cpu 个数
            socket_count = int(parser.get_value(r"Socket\(s\)[ :]+(\d+)"))
            self.assertEqual(ErrorCode.CUTCH001, f"cpu socket count", socket_count, e_socket_count)

            # cpu 型号
            model_name = parser.get_value(r"Model name[ :]+([\S ]+)")
            self.assertIn(ErrorCode.CUTCH002, f"cpu model name", e_model_name, model_name)


if __name__ == '__main__':
    runner.single_runner(FuncCpuCheck)
