# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   OamPowerFw_Bat.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re

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

from Lib.Result import Pass
from Lib.Template import TempItem
from Lib.Runner import runner


class OamPowerFw_Bat(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Oam power fw update"
        self.expect = "This is oam power fw Update."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        path = self.config["InitPath"]
        pmbus_list = []
        flag_ = False
        target_dict = {'ver': '0x3','ocl1': '0x2186', 'CRC': '0xf522'}
        with self.ssh_connect(uut=self.config["UUT"]):
            for dev in range(8):
                dict_ = {'dev': '', 'ver': '','ocl1': '', 'CRC': ''}
                dict_['dev'] = dev
                parser = self.execute_run(f"ppudbg --mpmbop read 0 0x20 1 0x9e --device {dev} | grep -o '0[xX][0-9a-fA-F]*'")
                dict_['ver'] = parser.get_origin_data().strip()
                parser = self.execute_run(f"ppudbg --mpmbop read 0 0x20 0 0xb9 --device {dev} | grep -o '0[xX][0-9a-fA-F]*'")
                dict_['ocl1'] = parser.get_origin_data().strip()
                parser = self.execute_run(f"ppudbg --mpmbop read 0 0x20 1 0xf0 --device {dev} | grep -o '0[xX][0-9a-fA-F]*'")
                dict_['CRC'] = parser.get_origin_data().strip()
                pmbus_list.append(dict_)
            if len(pmbus_list) == 0:
                self.fail("Get pmbus info fail")
            self.logger.info(pmbus_list)
            for pmbus in pmbus_list:
                if pmbus['ver'] != "0x3":
                    parser = self.execute_run(f'''ppudbg --mpmbop write 0 0x20 1 0x9e 0x03 "force" --device {pmbus['dev']}''')
                    if not re.search(r'pmbus\s*operation\s*successful', parser.get_origin_data(), re.I):
                        self.fail(f"Device:{pmbus['dev']} power pmbus operation fail, for ver")
                    self.sleep(1)
                if pmbus['ocl1'] != "0x2186":
                    parser = self.execute_run(f'''ppudbg --mpmbop write 0 0x20 0 0xb9 0x2186 "force" --device {pmbus['dev']}''')
                    if not re.search(r'pmbus\s*operation\s*successful', parser.get_origin_data(), re.I):
                        self.fail(f"Device:{pmbus['dev']} power pmbus operation fail, for ocl1")
                    self.sleep(1)
                if pmbus['CRC'] != "0xf522":
                    parser = self.execute_run(f'''ppudbg --mpmbop write 0 0x20 1 0xf0 0xf522 "force" --device {pmbus['dev']}''')
                    if not re.search(r'pmbus\s*operation\s*successful', parser.get_origin_data(), re.I):
                        self.fail(f"Device:{pmbus['dev']} power pmbus operation fail, for CRC")
                    self.sleep(1)
                parser = self.execute_run(f'''ppudbg --mi2cop write 1 0x20 0x17 0 0 --device {pmbus['dev']}''')
                if not re.search(r'operation\s*successful', parser.get_origin_data(), re.I):
                    self.fail(f"Device:{pmbus['dev']} program dul fail")
                self.sleep(1)

            self.execute_run("modprobe -r alixpu && modprobe alixpu")        
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(OamPowerFw_Bat)

