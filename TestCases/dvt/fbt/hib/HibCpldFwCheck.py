# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   HibCpldFwCheck.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re

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


class HibCpldFwCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpld fw check"
        self.expect = "This is cpld fw check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def exe(self):
        FwVsersion = self.config["FwVsersion"]

        with self.ssh_connect(uut=self.config["BMC_TAIL"]):
            # check HIB fw verion
            self.logger.info("========================check hib fw version===========================")
            parser = self.execute_run("i2ctransfer -y 11 w2@0x10 0x00 0x05 r1")
            self.logger.info(f"target version: {FwVsersion['hib_ver']}")
            self.assertEqual("check hib cpld fw version", parser.get_origin_data().strip(), FwVsersion.get("hib_ver"))

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(HibCpldFwCheck)

