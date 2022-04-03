# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Harvey
@Software:   TestCase
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import os
import re
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

from Lib.Result import Pass
from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Constant import ErrorCode


class OamPowerFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpu config check"
        self.expect = "This is cpu config check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key": "BMC_02"},
            {"folder": "LuxAncoanPT/100/Config","file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "LuxAncoanPT/100/Config","file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        oam_power_ver = self.config["FwVsersion"]["oampower_ver"]
        oam_power_update_file = self.config["InitPath"]["oam_update_file"]
        with self.ssh_connect(uut=self.config["UUT"]):
            for i in range(8):
                data = self.execute_run(f"ppudbg --mpmbop read 0 0x20 1 0x9e --device {i} ", i_exit_code=True).data
                data = re.findall("Read result value.*", data, re.I)
                if data:
                    data = data[0].split(':')[1].strip()
                else:
                    self.fail(self)
                if data != oam_power_ver:
                    cmd = f"ppudbg --pmbdev mp2891 {oam_power_update_file} --device {i}"
                    self.execute_run(cmd, i_exit_code=True)
                    new_data = self.execute_run(f"ppudbg --mpmbop read 0 0x20 1 0x9e --device {i} ", i_exit_code=True).data
                    data = re.findall("Read result value.*", new_data, re.I)
                    if data:
                        data = data[0].split(':')[1].strip()
                    else:
                        self.fail(self)
                    self.assertEqual(ErrorCode.FFFFFFFF,f" Hib Chassis Board Serial ", data, oam_power_ver)
            # self.assertEqual(f"clear bmc sel log", int(1), len(count)))


if __name__ == '__main__':
    runner.single_runner(OamPowerFwUpdate)

