# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   BiosFwCheck.py
@Time    :   2022/2/1
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
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


class BiosFwCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "bios fw check"
        self.expect = "This is bios fw check."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": "BMC_01"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def exe(self):
        target_bios_ver = self.config["FwVsersion"]["bios_ver"]
        with self.ssh_connect(uut=self.config["UUT"]):
            parser = self.execute_run("dmidecode -t bios | grep -i version | awk '{print $2}'")
            self.assertEqual(ErrorCode.FFFFFFFF, "check bios fw version", parser.get_origin_data(), target_bios_ver)
        


if __name__ == '__main__':
    runner.single_runner(BiosFwCheck)

