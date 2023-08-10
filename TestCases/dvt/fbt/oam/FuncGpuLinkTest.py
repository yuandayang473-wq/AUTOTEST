# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncGpuLinkTest.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/GPULinkTest
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


class FuncGpuLinkTest(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "GPU Link"
        self.expect = "This is GPU Link function check test"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "oam_conf", "key": "OAM"},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
        ]

    def exe(self):
        jbog = self.config["cfg"]["JBOG"]
        oam_config = self.config["oam_conf"]
        links = oam_config['Link']
        with self.ssh_connect(uut=self.config["UUT"]):
            if jbog["config"] == "W/O scaleout":
                for n in oam_config["Num"]:
                    with self.action(f"device: {n}"):
                        for p in links["not-scale-out"]:
                            parser = self.execute_run(f"ppudbg --device {n} --micnop stat {p}")
                            status = parser.get_value("Link Status[: ]+(up)")
                            self.assertEqual(f"oam device {n} ICN link state:", status.lower(), "up")
            else:
                for n in oam_config["Num"]:
                    with self.action("device: {n}"):
                        for p in links["scale-out"]:
                            parser = self.execute_run(f"ppudbg --device {n} --micnop stat {p}")
                            status = parser.get_value("Link Status[: ]+(up)")
                            self.assertEqual(f"oam device {n} ICN link state:", status.lower(), "up")

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(FuncGpuLinkTest)
