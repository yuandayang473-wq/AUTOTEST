# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   OamFwUpdate.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re

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


class OamFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Oam fw update"
        self.expect = "This is oam fw Update."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": "BMC_01"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        target_oam_ver = self.config["FwVsersion"]["oam_ver"]
        path = self.config["InitPath"]
        with self.ssh_connect(uut=self.config["UUT"]):
            for dev in range(8):
                parser = self.execute_run(f"ppudbg --device {dev} | grep -i 'Firmware Version' | cut -d' ' -f3")
                if parser.get_origin_data().strip() != target_oam_ver:
                    parser = self.execute_run(f"rpm -ivh  {path['oam_fw']} --force --nodeps")
                    if not re.search(r'upgrade successfully ', parser.get_origin_data(), re.I):
                        self.logger.info("Oam fw flash bure fail")
                        self.fail(ErrorCode.FFFFFFFF, "Oam fw flash bure fail")
                    break



if __name__ == '__main__':
    runner.single_runner(OamFwUpdate)

