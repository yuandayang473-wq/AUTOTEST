# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   NicFwUpdate.py
@Time    :   2023/5/9
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
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


class NicFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "nic fw update"
        self.expect = "This is nic fw update."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": "BMC_01"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        target_mcx_ver = self.config["FwVsersion"]["mcx6_ver"]
        path = self.config["InitPath"]
        with self.ssh_connect(uut=self.config["UUT"]):
            # mcx6
            parser = self.execute_run("lspci -Dnn | grep -i 15b3 | grep -i 'ConnectX-6' | awk '{print $1}'")
            nic_list = parser.filter_list(r"[\w]{4}:[\w]{2}:[\w]{2}.0")
            for nic_bus in nic_list:
                # 查询版本
                parser = self.execute_run(f"ls /sys/bus/pci/devices/{nic_bus}/net | xargs -I nic_port ethtool -i nic_port | grep -i 'firmware-version' | cut -d' ' -f2")
                if parser.get_origin_data() != target_mcx_ver:
                    self.execute_run(f"flint -d {nic_bus} -i {path.get('nic_fw')} -y b", i_exit_code=True)

        


if __name__ == '__main__':
    runner.single_runner(NicFwUpdate)

