# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   RetimeFwUpdate.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re
import binascii

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


class RetimeFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Retimer fw Update"
        self.expect = "This is retimer fw Update."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": "BMC_01"},
            {"file": "BmcDevice.yaml", "name": "BMC_HEADER", "key": "BMC_03"},
            {"folder": "LuxAncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        tail_bmc_ip = self.config["BMC_TAIL"]["ip_address"]
        header_bmc_ip = self.config["BMC_HEADER"]["ip_address"]
        FwVsersion = self.config["FwVsersion"]
        path = self.config["InitPath"]

        user = {
            "ip_address": "localhost",
            "password": "123456",
            "username": "root"
        }
        
        with self.ssh_connect(uut=self.config["BMC_TAIL"]):
            parser = self.execute_run("ls /var/retimer/ | xargs")
            retimers = parser.get_origin_data().split(" ")
            ven = parser.get_origin_data().split(" ")[0]
            self.logger.info(ven)
            from_ = 'tail_m' if 'm' in ven else 'tail_a'
            parser = self.execute_run("ipmitool raw 0x3e 0x07 0x00 0x4c 0xa5 0x07 0x03 1 9")
            self.logger.info(str(binascii.a2b_hex(parser.get_origin_data().replace(' ', '')))[6:-1])
            current_ver = str(binascii.a2b_hex(parser.get_origin_data().replace(' ', '')))[6:-1]
        with self.ssh_connect(uut=user):
            for retimer in retimers:
                print(retimer)
            # if current_ver != FwVsersion['retimer_ver']:
            #     parser = self.execute_run(f"{path['retimer_script']} {tail_bmc_ip} {path['retimer_fw'][from_]}")
        


if __name__ == '__main__':
    runner.single_runner(RetimeFwUpdate)

