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
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        header_bmc_ip = self.config["BMC_HEADER"]["ip_address"]
        FwVsersion = self.config["FwVsersion"]
        path = self.config["InitPath"]
        count = 1

        info = {}
        with self.ssh_connect(uut=self.config["BMC_HEADER"]):
            for num in range(1, 9):
                parser = self.execute_run(f"ipmitool raw 0x3e 0x07 0x00 0x4c 0xa5 0x07 0x03 {num} 9",
                                          parser_type="raw_parser")
                flag = parser.raw_str(0)

                from_ = "header_m" if flag.lower() == "0b" else "header_a"

                current_ver = str(binascii.a2b_hex(parser.get_origin_data().replace(' ', '')))[6:-1]
                # self.logger.info(current_ver)
                info[num] = (current_ver, from_)

        with self.ssh_connect(uut=self.config["UUT"]):
            for num in range(1, 9):
                cur_version = info[num][0].lower()
                from_ = info[num][1].strip().lower()
                # 比较版本
                if cur_version != FwVsersion['retimer_ver'][from_].strip().lower():
                    self.logger.info(f"ls {path['retimer_fw'][from_]}")
                    while count < 3:
                        cmd = f"{path['retimer_script']} {header_bmc_ip} taobao 9ijn0okm {path['retimer_fw'][from_]} {num}"
                        self.execute_run(cmd)
                        if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                            break
                        count += 1
                    else:
                        self.logger.info("head retimer flash fail")
                        self.fail(ErrorCode.FWTUP00F, "head retimer flash fail")

        


if __name__ == '__main__':
    runner.single_runner(HeaderRetimerFwUpdate)

