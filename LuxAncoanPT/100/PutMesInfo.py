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
import re
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
from Utils.Constant import TypeCode
from Lib.Request import MesSocket



class PutMesInfo(TempItem):

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
            _mes = MesSocket()
            output = self.execute_run("ipmitool lan print ").data
            output = re.findall("mac address.*", output, re.I)[0]
            mac_info = output.split(' : ')[1].strip()
            output = self.execute_run("ipmitool fru ").data
            chassis_sn_output = re.findall("Chassis Serial.*", output, re.I)[0]
            chassis_sn = chassis_sn_output.split(' : ')[1].strip()
            tdid_output = re.findall("product asset tag.*", output, re.I)[0]
            tdid_info = tdid_output.split(' : ')[1].strip()
            data = {
                    "cmd": "UPLOAD",
                    "server_tdid": tdid_info,
                    "server_sn": chassis_sn,
                    "server_mac": mac_info}
            self.logger.info(data)
            _mes.station_crossing(data)
        


if __name__ == '__main__':
    runner.single_runner(PutMesInfo)

