# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   HibFanSpeedChcek.py
@Time    :   2023/5/9
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/Fan测试/风扇调速测试 (机尾)
'''
import os
import sys

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
from Utils.BmcUtility import multi_column
from Utils.DataBuffer import StrParser


class HibFanSpeedChcek(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "fan speed"
        self.expect = "This is fan speed function check test"

        self.config = [
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
        ]

    def exe(self):
        JBOG = self.config["cfg"]["JBOG"]
        pwm_value = " 0x64" * JBOG["fan_count"]
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            self.execute_run("ipmitool raw 0x3e 0x21 0 0x4c 0xa5 1 2 0xff 0xff 0xff 0xff", desc="")
            if JBOG["config"] == "W/O scaleout":
                cmd = "ipmitool sdr list |grep -iE '^fan' |grep -i PWM"
            else:
                cmd = "ipmitool sdr list |grep -i 'fan' |grep -i PWM"
            self.execute_run("ipmitool sdr list |grep -i fan |grep -i 'PWM'")
            self.execute_run(f"ipmitool raw 0x3e 0x23 0 0x4c 0xa5 1{pwm_value}")
            self.sleep(60)
            parser = self.execute_run(cmd)
            fan_pwms = multi_column(parser.get_origin_data(), column_index=[0, 1])
            for name, value in fan_pwms:
                v = StrParser(value).get_value(r"(\d+)[ ]+percent")
                self.assertEqual(f"{name}", v, "100")
            self.execute_run("ipmitool raw 0x3e 0x21 0x00 0x4C 0xA5 0x01 0x01")
            self.sleep(60)
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(HibFanSpeedChcek)
