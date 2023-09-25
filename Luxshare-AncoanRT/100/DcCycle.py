# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Harvey
@Contact :   Harvey@luxshare-ict.com
@Software:   TestCase
@File    :   FuncCpuCheck.py
@Time    :   2023/5/4
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/CPU测试 （机头）
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


class DcCycle(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpu"
        self.expect = "This is cpu function check test on the service"
        self.config = [
        ]

    def exe(self):
        data = self.platform.get_platform_data()
        self.logger.info(data)

        header_bmc_ip = data["BMC_03"]["ip_address"]
        tail_bmc_ip = data["BMC_01"]["ip_address"]

        self.logger.info("server dc cycle off")
        self.os_run.run(f"ipmitool -I lanplus -H {header_bmc_ip} -U taobao -P 9ijn0okm power off")
        self.logger.info("jbog dc cycle ")
        self.os_run.run(f"ipmitool -I lanplus -H {tail_bmc_ip} -U admin -P admin chassis power cycle")
        self.sleep(120)
        self.os_run.run(f"ipmitool -I lanplus -H {header_bmc_ip} -U taobao -P 9ijn0okm power on")
        if not self.platform.check_uut(action="on"):
            self.fail(ErrorCode.FFFFFFFF, "uut poweron fail")


if __name__ == '__main__':
    runner.single_runner(DcCycle)
