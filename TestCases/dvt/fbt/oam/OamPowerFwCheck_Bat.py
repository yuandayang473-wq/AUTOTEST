# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   OamPowerFwCheck_Bat.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
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
from TestCases.dvt.common.Constant import OAM_UBB_SLOT_DEVICE


class OamPowerFwCheck_Bat(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Oam Power Fw check"
        self.expect = "This is oam power fw update."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        # path = self.config["InitPath"]
        # pmbus_list = []
        # flag_ = False
        # target_dict = {'ver': '0x3','ocl1': '0x2186', 'CRC': '0xf522'}
        # suite = self.parent
        # ubb = suite.globals["UBB"]
        # oam_sn = ubb["Results"]["oam_sn"]
        # if oam_sn:
        with self.ssh_connect(uut=self.config["UUT"]):
            # for oam in oam_sn:
            for dev in range(8):
                parser = self.execute_run(f"ppudbg --mpmbop read 0 0x20 1 0x9e --device {dev} | grep -o '0[xX][0-9a-fA-F]*'")
                if "0x3" != parser.get_origin_data().strip():
                    self.fail(f"Device:{dev} check pmbus info fail, for ver")
                parser = self.execute_run(f"ppudbg --mpmbop read 0 0x20 0 0xb9 --device {dev} | grep -o '0[xX][0-9a-fA-F]*'")
                if "0x2186" != parser.get_origin_data().strip():
                    self.fail(f"Device:{dev} check pmbus info fail, for ocl1")
                parser = self.execute_run(f"ppudbg --mpmbop read 0 0x20 1 0xf0 --device {dev} | grep -o '0[xX][0-9a-fA-F]*'")
                if "0xf522" != parser.get_origin_data().strip():
                    self.fail(f"Device:{dev} check pmbus info fail, for CRC")
            self.execute_run("modprobe -r alixpu && modprobe alixpu")
                    
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(OamPowerFwCheck_Bat)

