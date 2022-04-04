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
from Utils.BmcUtility import multi_column,a_column


class PowerOnHoursCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "bmc fw check"
        self.expect = "This is bmc fw check."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
        ]

    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            self.step(1, "get m.2 info")
            parser = self.execute_run("lsblk | grep sd", i_exit_code=True, retry_expt=1)
            self.step(2, "check m.2 info")
            disks = []
            if parser.get_origin_data() != "Null":
                m2s = multi_column(parser.get_origin_data(), column_index=[0, 3, 5], separator=" ")
                for m in m2s:
                    m2_name = m[0]
                    m2_type = m[2]
                    if m2_type == 'disk':
                        m2_size = float(m[1][:-1])
                        if m2_size >= 100.0:
                            disks.append(m2_name)

            for disk in disks:
                parser = self.execute_run(f"smartctl -s on --all /dev/{disk} | grep Power_On_Hours")
                hours = a_column(parser.get_origin_data(), column_index=-1, separator=" ")[0]
                if float(hours) > 500:
                    flag = input(f"/dev/{disk} 硬盘使用时间超过500小时，请更换机头继续测试。(y/n)")
                    if flag.lower() == 'y':
                        break
                    else:
                        self.fail(f"stop /dev/{disk} power on hours")

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(PowerOnHoursCheck)

