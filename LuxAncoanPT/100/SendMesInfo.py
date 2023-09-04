
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
import re
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


class SendMesInfo(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "iperf test"
        self.expect = "This is iperf test for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "Iperf", "key": "Iperf"},{"file": "BmcDevice.yaml", "name": "JBMC", "key":"BMC_02"},
        ]

    def exe(self):
        
        with self.ssh_connect(uut=self.config["UUT"]):
            _mes = MesSocket()
            _server_sn =  _mes.get_mes_info(self.parent.globals["SN"])["Results"]["server_sn"]
            _server_tdid =  _mes.get_mes_info(self.parent.globals["SN"])["Results"]["server_tdid"]
            data = self.execute_run("ipmitool lan print ").data
            _info = re.findall("MAC Address", data, re.I)
            print(_info)
        


if __name__ == '__main__':
    runner.single_runner(SendMesInfo)

