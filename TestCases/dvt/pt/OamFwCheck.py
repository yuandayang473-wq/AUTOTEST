# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   OamFwCheck.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
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


class OamFwCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Oam fw check"
        self.expect = "This is oam fw check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def exe(self):
        target_oam_ver = self.config["FwVsersion"]["oam_ver"]
        with self.ssh_connect(uut=self.config["UUT"]):
            for dev in range(8):
                parser = self.execute_run(f"ppudbg --device {dev} | grep -i 'Firmware Version' | cut -d' ' -f3")
                self.assertEqual(f"check oam-device{dev} version", parser.get_origin_data().strip(), target_oam_ver)
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(OamFwCheck)

