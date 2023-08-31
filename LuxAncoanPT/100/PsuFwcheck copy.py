# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   PsuFwcheck.py
@Time    :   2022/5/7
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


class PsuFwcheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "nic fw check"
        self.expect = "This is psu fw check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": "BMC_01"},
            {"file": "PSU.yaml", "name": "PSU", "key": "PSU"},
        ]

    def exe(self):
        tail_bmc_ip = self.config["BMC_TAIL"]["ip_address"]
        psu = self.config["PSU"]
        with self.ssh_connect(uut=self.config["UUT"]):
            for i in range(6):
                parser = self.execute_run(f"sshpass -p superuser ssh sysadmin@{tail_bmc_ip} -o StrictHostKeyChecking=no {psu['psu_cmd'].get(i)}")
                self.assertEqual(ErrorCode.FFFFFFFF, f"check psu{i+1} fw version", parser.get_origin_data(), psu.get(f"psu{i+1}_ver"))
        


if __name__ == '__main__':
    runner.single_runner(PsuFwcheck)

