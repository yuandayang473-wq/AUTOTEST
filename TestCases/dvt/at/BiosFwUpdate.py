# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   BiosFwUpdate.py
@Time    :   2022/2/1
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


class BiosFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "bios fw check for at"
        self.expect = "This is bios fw update for at."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "BmcDevice.yaml", "name": "HEADER_TAIL", "key": self.locals["HEAD_BMC"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def exe(self):
        path = self.config["InitPath"]
        header_bmc_ip = self.config["HEADER_TAIL"]["ip_address"]
        target_bios_ver = self.config["FwVsersion"]["bios_ver_for_at"]
        with self.ssh_connect(uut=self.config["UUT"]):
            parser = self.execute_run("dmidecode -t bios | grep -i version | awk '{print $2}'")
            if parser.get_origin_data() != target_bios_ver:
                parser = self.execute_run("chmod +x /opt/Alioam/fw/bios/*")
                parser = self.execute_run(f"{path.get('bios_Script')} {header_bmc_ip} taobao 9ijn0okm {path.get('bios_fw_for_at')} 1")
                if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                    self.logger.info("Header bios flash bure fail")
                    self.fail("Header bios flash bure fail")
            parser = self.execute_run("ipmitool chassis bootdev none options=clear-cmos")
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(BiosFwUpdate)

