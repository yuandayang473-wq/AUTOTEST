# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   HeaderRetimerFwUpdate.py
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


class HeaderRetimerFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Header Retimer fw Update"
        self.expect = "This is header retimer fw Update."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": "BMC_01"},
            {"file": "BmcDevice.yaml", "name": "BMC_HEADER", "key": "BMC_03"},
            {"folder": "LuxAncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        header_bmc_ip = self.config["BMC_HEADER"]["ip_address"]
        FwVsersion = self.config["FwVsersion"]
        path = self.config["InitPath"]
        count = 1

        with self.ssh_connect(uut=self.config["BMC_HEADER"]):
            parser = self.execute_run("ls /var/retimer/ | xargs")
            retimers = parser.get_origin_data().split(" ")
            ven = retimers[0]
            self.logger.info(ven)
            from_ = 'header_m' if 'm' in ven else 'header_a'
            parser = self.execute_run('''ipmitool alioem version | grep -i retimer | awk '{print $1"="$NF}' | xargs ''')
            current_versions = parser.get_origin_data().split()
            self.logger.info(current_versions)

        with self.ssh_connect(uut=self.config["UUT"]):
            for ver in current_versions:
                if ver:
                    remiter = ver.split("=")
                    name = remiter[0].strip().lower()
                    cur_version = remiter[1].strip().upper()
                    # 比较版本
                    if cur_version != FwVsersion['retimer_ver'][from_].upper():
                        self.logger.info(f"ls {path['retimer_fw'][from_]}")
                        while count < 3:
                            cmd = f"{path['retimer_script']} {header_bmc_ip} taobao 9ijn0okm {path['retimer_fw'][from_]} {name[-1]}"
                            self.execute_run(cmd)
                            if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                                break
                            count += 1
                        else:
                            self.logger.info("head retimer flash fail")
                            self.fail(ErrorCode.FWTUP00F, "head retimer flash fail")

        


if __name__ == '__main__':
    runner.single_runner(HeaderRetimerFwUpdate)

