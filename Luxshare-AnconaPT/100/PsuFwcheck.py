# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   PsuFwcheck.py
@Time    :   2022/5/7
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import binascii
import codecs

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


class PsuFwcheck(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "nic fw check"
        self.expect = "This is psu fw check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": "BMC_01"},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.mes_info["info"]["rk"]},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def exe(self):
        header_psu_count = self.config["cfg"]["SERVER"]["psu_count"]
        tail_psu_count = self.config["cfg"]["JBOG"]["psu_count"]
        FwVsersion = self.config["FwVsersion"]
        # tail
        with self.ssh_connect(self.config["BMC_TAIL"]):
            psu_count = int(self.execute_run("ipmitool sdr list | grep -ic ps.*power").get_origin_data())
            if psu_count != tail_psu_count:
                self.fail(ErrorCode.FFFFFFFF, "Tail pus count not match please check")
            for i in range(psu_count):
                parser = self.execute_run(f"ipmitool raw 0x3E 0x07 0x00 0x4C 0xA5 0x07 0x07 0x0{i+1} 0x06")
                current_tail_psuver = str(codecs.decode(binascii.a2b_hex(parser.get_origin_data().replace(' ', ''))))[1:]
                self.logger.info(current_tail_psuver)
                self.assertEqual(ErrorCode.FFFFFFFF, f"check psu{i+1} fw version", current_tail_psuver, FwVsersion["psu"]["tail_psu"])
        # header
        with self.ssh_connect(uut=self.config["UUT"]):
            parser = self.execute_run('''ipmitool alioem getdeviceinformation | grep -i FWVersion | awk '{print $1""$NF}' | xargs''')
            header_psu_versions = parser.get_origin_data().split(' ')
            if (header_psu_count != len(header_psu_versions)):
                self.fail(ErrorCode.FFFFFFFF, "Header pus count not match please check")
            for index, ver in enumerate(header_psu_versions):
                self.assertEqual(ErrorCode.FFFFFFFF, f"check psu{index+1} fw version", ver.split(":")[1].strip(), FwVsersion["psu"]["header_psu"])
        


if __name__ == '__main__':
    runner.single_runner(PsuFwcheck)

