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

from Lib.Result import Pass, Fail
from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Constant import ErrorCode
from Utils.Constant import TypeCode
from Lib.Request import MesSocket


class ServerProductName(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpu config check"
        self.expect = "This is cpu config check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key":"BMC_02"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "ServerProductNameModel", "key": "ServerProductNameModel"}

        ]

    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):

            _mes = MesSocket()
            rk_pn =  _mes.get_mes_info(self.parent.globals["SN"])["Results"]["rk_part_number"]
            list1 = self.config["ServerProductNameModel"]['AliServer-Xuanwu2.0-0323-2URG52PF']
            list2 = self.config["ServerProductNameModel"]['AS2211TG5']
            if rk_pn in list1:
                write_info = "AliServer-Xuanwu2.0-0323-2URG52PF"
            elif rk_pn in list2 :
                write_info = "AS2211TG5" 
            else:
                self.logger.error(f'not found {rk_pn} in server product name model')
                self.fail(TypeCode.FFFFFFFF, "No model found")
            #表格还未收集到
            data = self.execute_run("ipmitool fru print 0 ")
            parser = self.execute_run(f" ipmitool fru edit 0 field p 1 {write_info}")
            data = self.execute_run("ipmitool fru print 0 ")
            parser = _mes.json_filter(data, "Product Name" )
            self.assertEqual(TypeCode.FFFFFFFF, f"Chassis Part Number ", write_info, parser)

            # self.assertEqual(TypeCode.FFFFFFFF, f"clear Server bmc sel log", int(1), len(count))
        


if __name__ == '__main__':
    runner.single_runner(ServerProductName)

