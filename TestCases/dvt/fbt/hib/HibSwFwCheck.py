# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   HibSwFwCheck.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys

load_list = ["PPU"]


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

from Lib.Result import Pass
from Lib.Template import TempItem
from Lib.Runner import runner


class HibSwFwCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "pcie oam switch"
        self.expect = "This is pcie oam switch function check test on the server"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
            {"file": "UUT.yaml", "name": "path", "key": "InitPath"},
        ]

    def exe(self):
        shangxing = self.config["cfg"]["JBOG"]["shangxing"]

        exp_ver = "2:3" if shangxing == 8 else "2:2"
        count = 1

        with self.ssh_connect(uut=self.config["UUT"]):
            self.invoke_run(f"{self.config['path']['pciesw_tool']}", end_with="connect with :")

            for i in range(1, 4):
                self.invoke_run(f"{i}", end_with="PEX89104 B0>")
                self.invoke_run("cli showmfg", end_with="PEX89104 B0>")
                self.invoke_run("list", end_with="connect with :")

            self.invoke_run("4", end_with="PEX89104 B0> ")
            self.invoke_run("cli showmfg", end_with="PEX89104 B0>")

            parser = self.invoke_run("quit", end_invoke=True)
            versions = parser.filter_list(r"Associated FW ver[: ]+\d:\d:(\d:\d)")
            for cur_ver in versions:
                self.assertEqual(f"switch {count} version", cur_ver, exp_ver)
                count += 1
            self.sleep(2)
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(HibSwFwCheck)

