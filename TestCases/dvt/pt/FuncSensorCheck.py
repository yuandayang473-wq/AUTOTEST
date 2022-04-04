# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncSensorCheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/Sensor测试/sensor检查
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
from Lib.Request import MesSocket

class FuncSensorCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "uart"
        self.expect = "This is uart function check test"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
        ]

    def exe(self):
        # 获取机头的sdr
        _mes = MesSocket()
        model_str =  _mes.get_mes_info(self.parent.globals["SN"])["Results"]["rk_part_number"]
        print(model_str)
        server = self.config["cfg"]["SERVER"]
        jbog = self.config["cfg"]["JBOG"]
        server_white_list = server["white_list"]
        jbog_white_list = jbog["white_list"]

        with self.ssh_connect(uut=self.config["UUT"]):
            data = self.execute_run("ipmitool sdr")
            data_list = data.split('\r\n')
            error_info = []
            # llist = []
            for info in data_list:
                if '| ok' not in info and info:
                    check = info.split()[0]
                    if check not in server_white_list:
                        error_info.append(info)
            # for i in error_info:
            #     if i :
            #         a = i.split()[0]
            #         llist.append(a)
            # print(llist)
            if error_info:
                self.fail(f"check server sdr list is fail : {error_info}")


        # 获取机尾的sdr
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            data = self.execute_run("ipmitool sdr")
            data_list = data.split('\r\n')
            error_info = []
            for info in data_list:
                if '| ok' not in info and info:
                    check = info.split()[0]
                    if check not in jbog_white_list:
                        error_info.append(info)
            
            if error_info:
                self.fail(f"check jbog sdr list is fail : {error_info}")

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(FuncSensorCheck)

