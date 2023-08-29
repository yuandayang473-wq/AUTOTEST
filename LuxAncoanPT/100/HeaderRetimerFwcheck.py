# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   HeaderRetimerFwcheck.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re
import binascii

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
from Utils.Constant import TypeCode


class HeaderRetimerFwcheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Header Retimer fw check"
        self.expect = "This is header retimer fw check for normal case."
        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": "BMC_02"},
            {"file": "BmcDevice.yaml", "name": "BMC_HEADER", "key": "BMC_03"},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def exe(self):
        tail_bmc_ip = self.config["BMC_TAIL"]["ip_address"]
        header_bmc_ip = self.config["BMC_HEADER"]["ip_address"]
        FwVsersion = self.config["FwVsersion"]
        
        with self.ssh_connect(uut=self.config["BMC_HEADER"]):
            parser = self.execute_run("ls /var/retimer/ | xargs")
            ven = parser.get_origin_data().split(" ")[0]
            self.logger.info(ven)
            from_ = 'header_m' if 'm' in ven else 'header_a'
            parser = self.execute_run('''ipmitool alioem version | grep -i retimer | awk '{print $1"="$NF}' | xargs ''')
            current_versions = parser.get_origin_data().split()
            for i in current_versions:
                self.logger.info(f"{i}")
                self.assertEqual(TypeCode.FFFFFFFF, "check head retimer fw version", i.split('=')[1].strip().lower(), FwVsersion['retimer_ver'][from_].strip().lower())
                
        


if __name__ == '__main__':
    runner.single_runner(HeaderRetimerFwcheck)

