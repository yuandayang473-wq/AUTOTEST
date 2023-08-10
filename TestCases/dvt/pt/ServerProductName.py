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

from Lib.Result import Pass, Fail
from Lib.Template import TempItem
from Lib.Runner import runner
from Lib.Request import MesSocket


class ServerProductName(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpu config check"
        self.expect = "This is cpu config check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key":self.locals["TAIL_TAOBAO_BMC"]},
        ]

    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):

            _mes = MesSocket()
            rk_pn =  _mes.get_mes_info(self.parent.globals["SN"])["Results"]["rk_part_number"]
            list1 = ["RK0037030011" ,"RK0037030004" ,"RK0037030018"]
            list2 = ["RK0037030007" ,"RK0037030001" ,"RK0037030014", "RK0037030020", "RK0037030024","RK0037030012","RK0037030025"]
            if rk_pn in list1:
                write_info = "AliServer-Xuanwu2.0-0323-2URG52PF"
            elif rk_pn in list2 :
                write_info = "AS2211TG5" 
            else:
                return Fail(self)
            #表格还未收集到
            data = self.execute_run("ipmitool fru print 0 ")
            parser = self.execute_run(f" ipmitool fru edit 0 field p 1 {write_info}")
            data = self.execute_run("ipmitool fru print 0 ")
            parser = _mes.json_filter(data, "Product Name" )
            self.assertEqual(f"Chassis Part Number ", write_info, parser)

            # self.assertEqual(f"clear Server bmc sel log", int(1), len(count))
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(ServerProductName)

