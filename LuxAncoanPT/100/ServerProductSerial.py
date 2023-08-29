
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
from Utils.Constant import TypeCode
from Lib.Request import MesSocket


class ServerProductSerial(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpu config check"
        self.expect = "This is cpu config check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key":"BMC_02"},
        ]

    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            _mes = MesSocket()
            #查看机头的三段码
            write_info =  _mes.get_mes_info(self.parent.globals["SN"])["Results"]["server_sn"]
            data = self.execute_run("ipmitool fru print 0 ").data.strip()
            parser = self.execute_run(f" ipmitool fru edit 0 field p 4 {write_info}")
            data = self.execute_run("ipmitool fru print 0 ").data.strip()
            parser = _mes.json_filter(data, "Product Serial" )
            self.assertEqual(TypeCode.FFFFFFFF, f"Chassis Part Serial ", write_info, parser)


            # self.assertEqual(TypeCode.FFFFFFFF, f"clear Server bmc sel log", int(1), len(count))
        


if __name__ == '__main__':
    runner.single_runner(ServerProductSerial)

