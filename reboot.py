# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@ins-ict.com
@Software:   TestCase
@File    :   BmcFwcheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©ins  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re
import time

# load_list = ["LuxScript"]


# def load_package(path):
#     parent_folder = os.path.dirname(path)
#     for dirname in os.listdir(parent_folder):
#         if dirname in load_list:
#             sys.path.append(os.path.join(parent_folder, dirname))
#             load_list.pop(load_list.index(dirname))
#         if not load_list:
#             return None
#     else:
#         return load_package(parent_folder)
#
#
# load_package(os.path.abspath(__file__))



class reboot(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "reboot"
        self.expect = "This is reboot."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
        ]

    def exe(self):
        ip = self.config["UUT"]["ip_address"]

        with self.ssh_connect(uut=self.config["UUT"]):
            base_log_name = "{}_pretest0.log".format(time.strftime("%Y%m%d_%H%M%S"))
            self.execute_run(
                "python3 fw_check.py |tee {}".format(base_log_name))
        for i in range(1, 5):
            self.logger.info("第{}次power cycle".format(i))
            with self.ssh_connect(uut=self.config["UUT"]):
                self.execute_run(
                    "ipmitool power cycle", i_exit_code=True)
            for j in range(20):
                time.sleep(25)
                self.os_run.run("ping -c 1 -w 1 {}".format(ip), i_exit_code=True)
                if self.os_run.get_exit_code() == 1:
                    break
            else:
                raise Exception("500S仍未连接")
            with self.ssh_connect(uut=self.config["UUT"]):
                log_name = "{}_powercycle{}.log".format(time.strftime("%Y%m%d_%H%M%S"), i)
                self.execute_run(
                "python3 fw_check.py |tee {}".format(log_name))
                self.execute_run(
                "diff {} {}".format(log_name, base_log_name))

        for i in range(1, 5):
            self.logger.info("第{}次reboot".format(i))
            with self.ssh_connect(uut=self.config["UUT"]):
                self.execute_run(
                    "reboot", i_exit_code=True)
            for j in range(20):
                time.sleep(25)
                self.os_run.run("ping -c 1 -w 1 {}".format(ip), i_exit_code=True)
                if self.os_run.get_exit_code() == 1:
                    break
            else:
                raise Exception("500S仍未连接")

            with self.ssh_connect(uut=self.config["UUT"]):
                log_name = "{}_reboot{}.log".format(time.strftime("%Y%m%d_%H%M%S"), i)
                self.execute_run(
                "python3 fw_check.py |tee {}".format(log_name))
                self.execute_run(
                "diff {} {}".format(log_name, base_log_name))



