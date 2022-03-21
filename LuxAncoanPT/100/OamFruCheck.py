# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   OamFruCheck.py
@Time    :   2023/7/27
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
from Utils.DataBuffer import StrParser


class OamFruCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "oam fru write"
        self.expect = "This is oam oam fru write."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": "BMC_02"},
        ]

    def exe(self):
        path = self.config["InitPath"]
        fru_path = path.get("fru_path")
        with self.ssh_outband_connect(uut=self.config["UUT"], bmc=self.config["BMC_TAIL"]):

            device_dict = {}
            for i in range(8):
                parser = self.execute_run(f" ppudbg --device {i} |grep -i moduleid")
                current_fruinfo = parser.get_value(r"ModuleId: (\d+)")
                device_dict[f'{int(current_fruinfo) + 1}'] = i

            parser = self.outband_run("ipmitool fru")
            ppus = parser.split(r'FRU Device Description[ :]+PPU')[1:]
            for ppu in ppus:
                ppu_parser = StrParser(ppu)
                solt_id = ppu_parser.get_value(r"(\d)+_FRU")
                sn1 = ppu_parser.get_value(r"Board Serial[ :]+(\w+)")
                device_id = device_dict[solt_id]

                parser = self.execute_run(f"python {fru_path}ppudbg_load_fru.py --function=read --device={device_id}")
                sn2 = parser.get_value(r"serial[ =]+(KS.*)")
                self.assertEqual(ErrorCode.FFFFFFFF, f"ppu device {device_id}", sn1, sn2)

        


if __name__ == '__main__':
    runner.single_runner(OamFruCheck)
