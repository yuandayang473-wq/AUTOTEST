# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   HibPcieDiskCheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/PCIE链路测试/Disk info check
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
from Utils.DataBuffer import StrParser


class HibPcieDiskCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "pcie disk"
        self.expect = "This is pcie disk function check test on the server"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "PCIE", "key": "Pcie"},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
        ]

    def exe(self):
        pcie_config = self.config["PCIE"]
        pcie_disk_config = pcie_config["NVME"]
        jbog_cfg = self.config["cfg"]["JBOG"]
        nvme_size = jbog_cfg["nvme_size"]

        if nvme_size == "NA":
            return Pass(self)

        with self.ssh_connect(uut=self.config["UUT"]):
            self.step(1, "get memory info")
            parser = self.execute_run(
                r"""lspci |grep -i Non-Vol |cut -d " " -f1 |xargs -I {} lspci -s {} -vvv |grep -iE 'Non-Vol|LnkSta'""")
            datas = parser.split(r"([0-9a-z]{4}:[0-9a-z]{2}:[0-9a-z]{2}\.[0-9a-z]{1})")
            for data in datas:
                if datas and len(data) == 12:
                    device = data
                elif data:
                    parser = StrParser(data)
                    speed = parser.get_value(r"Speed ([0-9]+GT/s)")
                    width = parser.get_value(r"Width (x[0-9]+)")
                    rst = parser.check_field("downgraded")
                    self.assertEqual(f"pcie disk {device} speed", speed, pcie_disk_config["Speed"])
                    self.assertEqual(f"pcie disk {device} width", width, pcie_disk_config["Width"])
                    self.assertFalse(f"pcie oam {device} check exist (downgrade) keyword", rst)

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(HibPcieDiskCheck)

