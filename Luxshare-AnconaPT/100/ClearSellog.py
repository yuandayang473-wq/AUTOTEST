# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Software:   TestCase
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import time

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
from Lib.Request import MesSocket


class ClearSellog(TempItem):
    def __init__(self):
        super().__init__()
        self.name = "cpu config check"
        self.expect = "This is cpu config check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": "BMC_01"},
            {"file": "BmcDevice.yaml", "name": "SERVER_BMC", "key": "BMC_03"},{"file": "BmcDevice.yaml", "name": "JBMC", "key":"BMC_02"},
        ]

    def exe(self):
        #清除机尾alioem sel
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            parser = self.execute_run("touch /logs/restorefactory")
            parser = self.execute_run("ipmitool raw 6 2")

        self.sleep(30)

        #清除机头alioem sel
        # with self.ssh_connect(uut=self.config["SERVER_BMC"]):
        #     parser = self.execute_run("touch /logs/restorefactory")
        #     parser = self.execute_run("ipmitool raw 6 2")
        # self.sleep(30)

        with self.ssh_connect(uut=self.config["UUT"]):
            jbmc_ip = self.config["JBMC"]["ip_address"]
            jbmc_user = self.config["JBMC"]["username"]
            jbmc_passwd = self.config["JBMC"]["password"]
            time.sleep(10)
            parser = self.execute_run(f"ipmitool -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} sel clear ")
        #清除机头alioem sel 机头 sel log
            parser = self.execute_run(" ipmitool alioem restoretomanufacturesetting ")
            time.sleep(120)
            self.execute_run("modprobe -r alixpu && modprobe alixpu")     
        


if __name__ == '__main__':
    runner.single_runner(ClearSellog)

