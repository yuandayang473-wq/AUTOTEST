# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujunchdng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   BmcFwUpdate.py
@Time    :   2022/2/1
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


class HibBmcFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "bmc fw update"
        self.expect = "This is bmc fw update for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        tail_bmc_ip = self.config["BMC_TAIL"]["ip_address"]
        target_tail_ver = self.config["FwVsersion"]["tail_bmc_ver_at"]
        path = self.config["InitPath"]
        # tail_bmc_ver_at
        with self.ssh_connect(uut=self.config["UUT"]):
            
            parser = self.execute_run("ls -l /opt/Alioam/")
            if 'x' not in parser.get_origin_data():
                self.execute_run("chmod -R 777 /opt/Alioam/")
            
            # 检查机尾bmc fw版本
            parser = self.execute_run(f"ipmitool -I lanplus -H {tail_bmc_ip} -U admin -P admin mc info | grep -i 'Firmware Revision'")
            mian_ver = re.search(r'\d+.\d+', parser.get_origin_data()).group().strip()
            parser = self.execute_run(f"ipmitool -I lanplus -H {tail_bmc_ip} -U admin -P admin mc info | grep -i -A1  'Aux Firmware Rev Info' | tail -n1")
            sub_ver = str(int(parser.get_origin_data().strip()[2:], 16))
            current_tail_ver = mian_ver + '.' + sub_ver
            self.logger.info(f"Current tail bmc version is {current_tail_ver}, target version is {target_tail_ver}")
            if current_tail_ver != target_tail_ver:
            #if True:
                #parser = self.execute_run("chmod -R 777 /opt/Alioam/")
                # parser = self.execute_run(
                #     f"{path['bmc_tail_script']} {tail_bmc_ip} taobao 9ijn0okm {path['bmc_tail_fw']} BMCAndConf 1")
                parser = self.execute_run(
                f"{path['bmc_tail_script']} {tail_bmc_ip} taobao 9ijn0okm {path['bmc_tail_fw_for_at']} BMCAndConf 1")
                if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                    self.logger.info("Tail bmc flash bure fail")
                    self.fail("Tail bmc flash bure fail")

            timeout = 0
            while True:
                self.sleep(30)
                timeout += 30
                parser = self.execute_run(f"ping {tail_bmc_ip} -c4", i_exit_code=True)
                if re.search(r'0\%\s*packet\s*loss', parser.get_origin_data(), re.I):
                    break
                if timeout > 300:
                    self.fail("Tail Bmc restart fail")
            self.sleep(60)
            # self.execute_run("ipmitool chassis policy always-on")
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(HibBmcFwUpdate)

