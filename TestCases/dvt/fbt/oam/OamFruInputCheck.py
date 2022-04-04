# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   HibBmcFwcheck.py
@Time    :   2023/5/6
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
from Utils.DataBuffer import StrParser


class OamFruInputCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "bmc fw check"
        self.expect = "This is bmc fw check."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key": self.locals["TAIL_TAOBAO_BMC"]},
        ]

    def exe(self):

        with self.ssh_connect(uut=self.config["JBMC"]):
            parser = self.execute_run("ipmitool fru")
            ppus = parser.split(r'FRU Device Description[ :]+PPU')[1:]
            for ppu in ppus:
                ppu_parser = StrParser(ppu)
                solt_id = ppu_parser.get_value(r"(\d)+_FRU")
                sn = ppu_parser.get_value(r"Board Serial[ :]+(\w+)")

                input_sn = input(f"请输入槽位 [{solt_id}] SN:")
                self.assertEqual(f"solt [{solt_id}] SN", sn, input_sn.strip())

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(OamFruInputCheck)
