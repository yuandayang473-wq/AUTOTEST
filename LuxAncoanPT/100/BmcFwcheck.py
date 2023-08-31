# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   BmcFwcheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
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


class BmcFwcheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "bmc fw check"
        self.expect = "This is bmc fw check."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": "BMC_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def exe(self):
        bmc_tail = self.config["BMC"]["ip_address"]
        target_header_ver = self.config["FwVsersion"]["header_bmc_ver"]
        target_tail_ver = self.config["FwVsersion"]["tail_bmc_ver"]

        with self.ssh_connect(uut=self.config["UUT"]):
            # 检查机尾bmc fw版本
            parser = self.execute_run(
                f"ipmitool -I lanplus -H {bmc_tail} -U admin -P admin mc info | grep -i 'Firmware Revision'")
            mian_ver = re.search(r'\d+.\d+', parser.get_origin_data()).group().strip()
            parser = self.execute_run(
                f"ipmitool -I lanplus -H {bmc_tail} -U admin -P admin mc info | grep -i -A1  'Aux Firmware Rev Info' | tail -n1")
            sub_ver = str(int(parser.get_origin_data().strip()[2:], 16))
            current_tail_ver = mian_ver + '.' + sub_ver
            self.assertEqual(ErrorCode.FFFFFFFF, "check bmc fw version", current_tail_ver, target_tail_ver)

            # 检查机头bmc fw版本 子版本校验
            parser = self.execute_run("ipmitool mc info | grep -i 'Firmware Revision' | awk '{print $4}'")
            main_ver = re.search(r'\d+.\d+', parser.get_origin_data()).group().strip()
            parser = self.execute_run("ipmitool mc info | grep -i -A1  'Aux Firmware Rev Info' | tail -n1")
            sub_ver = str(int(parser.get_origin_data().strip()[2:], 16))
            current_header_ver = main_ver + '.' + sub_ver
            # 检查机头bmc fw版本 无子版本校验
            # parser = self.execute_run("ipmitool mc info | grep -i 'Firmware Revision' | awk '{print $4}'")
            # current_header_ver = re.search(r'\d+.\d+', parser.get_origin_data()).group().strip()
            self.assertEqual(ErrorCode.FFFFFFFF, "check bmc fw version", current_header_ver, target_header_ver)

        


if __name__ == '__main__':
    runner.single_runner(BmcFwcheck)

