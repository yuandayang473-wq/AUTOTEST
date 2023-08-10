# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   TailRetimerFwUpdate.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re
import binascii

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


class HibTailRetimerFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Tail Retimer fw Update"
        self.expect = "This is tail retimer fw Update."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        tail_bmc_ip = self.config["BMC_TAIL"]["ip_address"]
        FwVsersion = self.config["FwVsersion"]
        path = self.config["InitPath"]
        count = 1
        retimer_dict = {}

        with self.ssh_connect(uut=self.config["BMC_TAIL"]):
            parser = self.execute_run("ls /var/retimer/ | xargs")
            retimers = parser.get_origin_data().split(" ")
            for retimer in retimers:
                parser = self.execute_run(f"ipmitool raw 0x3e 0x07 0x00 0x4c 0xa5 0x07 0x03 {retimer[-1]} 9")
                current_ver = str(binascii.a2b_hex(parser.get_origin_data().replace(' ', '')))[6:-1]
                retimer_dict[retimer] = current_ver

        self.logger.info(retimer_dict)
        with self.ssh_connect(uut=self.config["UUT"]):
            for retimer, current_ver in retimer_dict.items():
                from_ = 'tail_m' if 'm' in retimer else 'tail_a'
                if current_ver.strip().lower() != FwVsersion['retimer_ver'][from_].strip().lower():
                    self.logger.info(f"ls {path['retimer_fw'][from_]}")
                    self.logger.info(
                        f"{path['retimer_script']} {tail_bmc_ip} admin admin {path['retimer_fw'][from_]} {retimer[-1]}")
                    while count < 3:
                        parser = self.execute_run(
                            f"{path['retimer_script']} {tail_bmc_ip} admin admin {path['retimer_fw'][from_]} {retimer[-1]}",
                            retry_expt=1,i_exit_code=True)
                        ret = parser.check_field(r"Flash[ ]+Complete")
                        if ret:
                            break
                        count += 1
                    else:
                        self.logger.info("tail retimer flash fail")
                        self.fail("tail retimer flash fail")
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(HibTailRetimerFwUpdate)

