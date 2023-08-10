# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   InitParams.py
@Time    :   2023/5/8
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   初始RK,必须要的参数
'''

import openpyxl
import os

from Lib.Config import YamlLoadConfig


class InitLoadConfig:
    """
    python3 BatchRun.py --put put[根据指定execl选择要测试机器]
    """

    def __init__(self):
        self.data = {}

    def load_config(self, put):
        # fileName 这里是指文件路径
        path_name = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Config")
        g = os.walk(path_name)
        for path, dir_list, file_list in g:
            for files_name in file_list:
                files = os.path.join(path, files_name)
                if '.xls' in files:
                    file_name = files
                    break
        wb = openpyxl.load_workbook(filename=file_name)
        sheet = wb.active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            put_name = row[0]
            if isinstance(put_name, str):
                if put_name.lower() == put.lower():
                    sn = row[2]
                    head_os_ip = row[4].strip()
                    head_bmc_ip = row[5].strip()
                    tail_bmc_ip = row[6].strip()
                    pdu_ip = row[7].strip()
                    pdu_head_port = row[8].strip()
                    pdu_tail_port = row[9].strip()
                    self.write_yaml(head_os_ip, head_bmc_ip, tail_bmc_ip, pdu_ip, pdu_head_port,
                                    pdu_tail_port)
                    return sn, put
        return None

    def write_yaml(self, head_os_ip, head_bmc_ip, tail_bmc_ip, pdu_ip, pdu_head_port, pdu_tail_port):
        device = YamlLoadConfig(cfg_path_name="Config", cfg_name="Device.yaml")
        bmc_device = YamlLoadConfig(cfg_path_name="Config", cfg_name="BmcDevice.yaml")
        pdu_device = YamlLoadConfig(cfg_path_name="Config", cfg_name="PduDevice.yaml")
        UUT = {
            "UUT_01": {
                "ip_address": head_os_ip,
                "username": "root",
                "password": '123456'
            }
        }
        bmc_data = {
            "BMC_01": {
                "ip_address": tail_bmc_ip,
                "username": "sysadmin",
                "password": 'superuser'
            },
            "BMC_02": {
                "ip_address": tail_bmc_ip,
                "username": "taobao",
                "password": '9ijn0okm'
            },
            "BMC_03": {
                "ip_address": head_bmc_ip,
                "username": "sysadmin",
                "password": 'superuser'
            }
        }
        pdu_data = {
            "PDU_01": {
                'ip_address': pdu_ip,
                'head_port': " ".join(pdu_head_port.split(",")),
                "tail_port": " ".join(pdu_tail_port.split(",")),
                'pdu_model': '1.3.6.1.4.1.23273.3.1.1.6',
            },
        }
        device.yaml_dump(UUT)
        bmc_device.yaml_dump(bmc_data)
        pdu_device.yaml_dump(pdu_data)

        self.data["UUT"] = UUT["UUT_01"]
        self.data["TAIL_ADMIN_BMC"] = bmc_data["BMC_01"]
        self.data["TAIL_TAOBAO_BMC"] = bmc_data["BMC_02"]
        self.data["HEAD_BMC"] = bmc_data["BMC_03"]
        self.data["PDU"] = pdu_data["PDU_01"]


if __name__ == '__main__':
    print(InitLoadConfig.load_config("put2"))
