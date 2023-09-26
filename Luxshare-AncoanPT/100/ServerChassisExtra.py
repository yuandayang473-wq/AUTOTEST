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

from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Constant import ErrorCode
from Utils.Init import load_mes_info
from Lib.Request import MesSocket



class ServerChassisExtra(TempItem):
    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "cpu config check"
        self.expect = "This is cpu config check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
        ]

    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            # 差一段三段码
            _mes = MesSocket(self.mes_info["info"]["url"],self.mes_info["info"]["sn"])
            part_number =  _mes.get_mes_info(self.mes_info["info"]["sn"])["Results"]["rk_customer_part_number"]
            part_number = part_number if part_number != "TG88M1S1V5X7WS.03ZA.C0V1P4U8" else "TG88M1S1V5X7WS.03ZA.C0V1"
            write_info = "AliType="+part_number
            data = self.execute_run("ipmitool fru print 0 ").data.strip()
            parser = self.execute_run(f"ipmitool fru edit 0 field c 2 '{write_info}' ")
            data = self.execute_run("ipmitool fru print 0 ").data.strip()
            parser = _mes.json_filter(data, "Chassis Extra" )
            
            self.assertEqual(ErrorCode.FFFFFFFF, f"Server Chassis Extra ", write_info, parser)

        


if __name__ == '__main__':
    runner.single_runner(ServerChassisExtra)

