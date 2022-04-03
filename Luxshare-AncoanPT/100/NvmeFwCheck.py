# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   NvmeFwCheck.py
@Time    :   2022/5/6
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


class NvmeFwCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "nvme fw check"
        self.expect = "This is nvme fw check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": "BMC_01"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        path = self.config["InitPath"]
        target_nvme_ver = self.config["FwVsersion"]["nvme_ver"]
        with self.ssh_connect(uut=self.config["UUT"]):
            parser = self.execute_run(f"chmod +x {path.get('nvme_tool')} && {path.get('nvme_tool')} list | grep -i 'INTEL' | " + '''awk '{print $1 "-" $NF}' | xargs ''')
            nvme_list = parser.get_origin_data().split()
            for nvme in nvme_list:
                self.assertEqual(ErrorCode.FFFFFFFF, f"check device {nvme.split('-')[0]} fw version", nvme.split('-')[1].strip(), target_nvme_ver.strip())
            # self.assertEqual(f"check device {parser.get_origin_data().split()[0]} fw version", parser.get_origin_data().split()[1], target_nvme_ver)
        


if __name__ == '__main__':
    runner.single_runner(NvmeFwCheck)

