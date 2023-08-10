# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Harvey
@Software:   TestCase
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import time

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
from Lib.Request import MesSocket


class ClearSellog(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Clear Sel log"
        self.expect = "This is clear Sel log for at."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "BmcDevice.yaml", "name": "SERVER_BMC", "key": self.locals["HEAD_BMC"]},{"file": "BmcDevice.yaml", "name": "JBMC", "key":self.locals["TAIL_TAOBAO_BMC"]},
        ]

    def exe(self):
        #清除机尾alioem sel
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            parser = self.execute_run("touch /logs/restorefactory")
            parser = self.execute_run("ipmitool raw 6 2")

        self.sleep(30)

        #清除机头alioem sel
        server_bmc = {
            'ip_address': self.config["SERVER_BMC"]["ip_address"],
            'username': 'taobao',
            'password': '9ijn0okm',
        }
        print(server_bmc)
        print("start clear header sel log")
        with self.ssh_connect(uut=server_bmc):
            parser = self.execute_run("ipmitool alioem restoretomanufacturesetting")

        self.sleep(30)

        user = {
            "ip_address": "localhost",
            "password": "1",
            "username": "root"
        }
        with self.ssh_connect(uut=user):
            jbmc_ip = self.config["JBMC"]["ip_address"]
            jbmc_user = self.config["JBMC"]["username"]
            jbmc_passwd = self.config["JBMC"]["password"]
            sbmc_ip = self.config["SERVER_BMC"]["ip_address"]
            sbmc_user = 'taobao'
            sbmc_passwd = '9ijn0okm'
            time.sleep(10)
            parser = self.execute_run(f"ipmitool -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} sel clear ")
            count = self.execute_run(f"ipmitool -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} sel list").data.strip().split('\n')
            self.assertEqual(f"clear Jbog bmc sel log", int(1), len(count))
            parser = self.execute_run(f"ipmitool -I lanplus -H {sbmc_ip} -U {sbmc_user} -P {sbmc_passwd} sel clear ")
            count = self.execute_run(f"ipmitool -I lanplus -H {sbmc_ip} -U {sbmc_user} -P {sbmc_passwd} sel list ").data.strip().split('\n')
            self.assertEqual(f"clear Server bmc sel log", int(1), len(count))
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(ClearSellog)

