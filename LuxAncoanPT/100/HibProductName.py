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


class HibProductName(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpu config check"
        self.expect = "This is cpu config check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key":"BMC_02"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "HibModel", "key": "HibModel"}
        ]

    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            jbmc_ip = self.config["JBMC"]["ip_address"]
            jbmc_user = self.config["JBMC"]["username"]
            jbmc_passwd = self.config["JBMC"]["password"]
            _mes = MesSocket()
            # rk_pn = self.parent.globals["SN"]/
            rk_pn =  _mes.get_mes_info(self.parent.globals["SN"])["Results"]["rk_part_number"]
            hib_model_list1 = self.config["HibModel"]['AliOGBOX-Xuanwu2.0-0323-6U8WS']
            hib_model_list2 = self.config["HibModel"]['AB0611OG1']
            hib_model_list3 = self.config["HibModel"]['AliOGBOX-Xuanwu2.0-0323-6U8WOS']
            if rk_pn in hib_model_list1:
                write_info = "AliOGBOX-Xuanwu2.0-0323-6U8WS"
            elif rk_pn in hib_model_list2 :
                write_info = "AB0611OG1" 
            elif rk_pn in hib_model_list3:
                write_info = "AliOGBOX-Xuanwu2.0-0323-6U8WOS"
            else:
                self.logger.error(f'not found {rk_pn} in hib model')
                self.fail(TypeCode.FFFFFFFF, "No model found")
                
            parser = self.execute_run(f" ipmitool -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru edit 0 field p 1 {write_info}")
            data = self.execute_run("ipmitool  -I lanplus -H %s -U %s -P %s  fru print 0 " % (jbmc_ip, jbmc_user ,jbmc_passwd), i_exit_code=True).data.strip()
            parser = _mes.json_filter(data, "Product Name" )
            self.assertEqual(TypeCode.FFFFFFFF, f"Hib Hib Product Name ", write_info, parser)
            # self.assertEqual(TypeCode.FFFFFFFF, f"clear Hib bmc sel log", int(1), len(count))
        


if __name__ == '__main__':
    runner.single_runner(HibProductName)

