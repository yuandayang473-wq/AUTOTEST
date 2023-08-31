# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   NicFwCheck.py
@Time    :   2022/2/1
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import os
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

from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Constant import ErrorCode


class NicFwCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "nic fw check"
        self.expect = "This is nic fw check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": "BMC_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "LuxAncoanPT/100/Config", "file": "FwVersion.yaml", "name": "DeviceCount", "key": "DEVICE_COUNT"},
            # {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": options.RK},
        ]

    def exe(self):
        target_mcx_ver = self.config["FwVsersion"]["mcx6_ver"]
        # header_count = 0 if self.config["cfg"]["SERVER"]["nic_type"] != "CX6" else self.config["cfg"]["SERVER"]["nic_count"]
        # tail_count = 0 if self.config["cfg"]["JBOG"]["nic_type"] != "CX6" else self.config["cfg"]["JBOG"]["nic_count"]
        with self.ssh_connect(uut=self.config["UUT"]):
            # mcx6网卡
            # parser = self.execute_run(" lspci -Dnn | grep -i 15b3 | grep -i 'ConnectX-6' | cut -d: -f2 | sort -u |xargs -I {} echo 0000:{}:00.0 | xargs")
            #             # nic_list = parser.get_origin_data().split()

            parser = self.execute_run("lspci -Dnn | grep -i 15b3 | grep -i 'ConnectX-6' | awk '{print $1}'")
            nic_list = parser.filter_list(r"[\w]{4}:[\w]{2}:[\w]{2}.0")
            if len(nic_list) != 0:
                for nic_bus in nic_list:
                    parser = self.execute_run(f"ls /sys/bus/pci/devices/{nic_bus}/net | xargs -I nic_port ethtool -i nic_port | grep -i 'firmware-version' | cut -d' ' -f2")
                    self.assertEqual(ErrorCode.FWTCH005, "check nic fw version", parser.get_origin_data(), target_mcx_ver)
            # mcx5网卡
            # parser = self.execute_run(" lspci -Dnn | grep -i 15b3 | grep -i 'ConnectX-5' | cut -d: -f2 | sort -u |xargs -I {} echo 0000:{}:00.0 | xargs")
            # nic_list = parser.get_origin_data().split()

            # parser = self.execute_run("lspci -Dnn | grep -i 15b3 | grep -i 'ConnectX-5' | awk '{print $1}'")
            # nic_list = parser.filter_list(r"[\w]{4}:[\w]{2}:[\w]{2}.0")
            #
            # if len(nic_list) != 0:
            #     for nic_bus in nic_list:
            #         parser = self.execute_run(f"ls /sys/bus/pci/devices/{nic_bus}/net | xargs -I nic_port ethtool -i nic_port | grep -i 'firmware-version' | cut -d' ' -f2")
            #         self.assertEqual("check nic fw version", parser.get_origin_data(), target_mcx_ver)

        


if __name__ == '__main__':
    runner.single_runner(NicFwCheck)

