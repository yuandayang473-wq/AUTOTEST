# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   HibBmcFwcheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys

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


class HibMacWrite(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "bmc fw check"
        self.expect = "This is bmc fw check."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key": self.locals["TAIL_TAOBAO_BMC"]},
        ]

    def exe(self):

        mac_str = self.parent.globals["HIB"]["Results"][0]["hib_mac"]
        mac = ""
        start = 0
        for s in range(2, len(mac_str) + 2, 2):
            mac += f"0x{mac_str[start:s]} "
            start = s

        with self.ssh_connect(uut=self.config["JBMC"]):
            # mac_str = "3043D73290A1"
            self.execute_run(f"i2ctransfer -y 7 w8@0x50 0x00 0x18 {mac.strip()}")
            self.execute_run("reboot", i_exit_code=True)
        self.sleep(60)

        return Pass(self)

    def tearDown(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            parser = self.execute_run("ipmitool -b 0x0a -t 0x32 lan print 1")
            tail_bmc_ip = parser.get_value(r"IP Address[ :]+((?:[0-9]+\.){3}[0-9]+)")

        suite = self.parent
        suite.globals["TAIL_TAOBAO_BMC"]["ip_address"] = tail_bmc_ip
        suite.globals["TAIL_ADMIN_BMC"]["ip_address"] = tail_bmc_ip
        tests = suite.get_tests()
        for test_list in tests.values():
            for test_class in test_list:
                test_class.locals["TAIL_TAOBAO_BMC"]["ip_address"] = tail_bmc_ip
                test_class.locals["TAIL_ADMIN_BMC"]["ip_address"] = tail_bmc_ip


if __name__ == '__main__':
    runner.single_runner(HibMacWrite)
