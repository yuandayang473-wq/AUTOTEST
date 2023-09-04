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
from Utils.Constant import TypeCode
from Lib.Request import MesSocket


class UbbBoardPartNumber(TempItem):

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
            jbmc_ip = self.config["JBMC"]["ip_address"]
            jbmc_user = self.config["JBMC"]["username"]
            jbmc_passwd = self.config["JBMC"]["password"]
            _mes = MesSocket()
            write_info =  _mes.get_mes_info(self.parent.globals["SN"])["Results"]["ubb_part_number"]
            # write_info = "805014087A01"
            # 差一段三段码
            data = self.execute_run("ipmitool  -I lanplus -H %s -U %s -P %s  fru print 5 " % (jbmc_ip, jbmc_user ,jbmc_passwd), i_exit_code=True).data
            parser = self.execute_run(f"ipmitool -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru edit 5 field b 3 '{write_info}' ", i_exit_code=True)
            data = self.execute_run("ipmitool  -I lanplus -H %s -U %s -P %s  fru print 5 " % (jbmc_ip, jbmc_user ,jbmc_passwd), i_exit_code=True).data
            parser = _mes.json_filter(data, "Board Part Number" )
            self.assertEqual(TypeCode.FFFFFFFF, f"Hib Board Part Number ", write_info, parser)
            # self.assertEqual(TypeCode.FFFFFFFF, f"clear bmc sel log", int(1), len(count))
        


if __name__ == '__main__':
    runner.single_runner(UbbBoardPartNumber)

