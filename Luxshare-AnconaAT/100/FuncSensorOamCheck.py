# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncSensorOamCheck.py
@Time    :   2023/5/8
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/Sensor测试/OAM Sensor检查
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


class FuncSensorOamCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "oam sensor"
        self.expect = "This is oam sensor function check test"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "Luxshare-AnconaAT/100/Config", "file": "UUT.yaml", "name": "oam", "key": "OAM"},
        ]

    def exe(self):
        oam_sensor_cfg = self.config["oam"]["Sensor"]
        oam_config = self.config["oam"]
        # 获取机头的sdr
        common_pattern = r"([\d\.]+)"
        with self.ssh_connect(uut=self.config["UUT"]):
            for n in oam_config["Num"]:
                # oam 温度
                cmd_getTemper = 'ppudbg --monitor power --time 1 --device {} '.format(n) + "| awk '{print $9}'"
                p = self.execute_run(cmd_getTemper)
                tem_value = float(p.get_value(common_pattern))
                self.assertLessEqual(ErrorCode.GPUTFT03, "oam temperature", tem_value, oam_sensor_cfg["max_temp"])
                self.assertGreaterEqual(ErrorCode.GPUTFT03, "oam temperature", tem_value, oam_sensor_cfg["min_temp"])

                # oam 功耗
                power = 'ppudbg --monitor power --time 1 --device {} '.format(n) + "| awk '{print $2}'"
                self.execute_run(power)
                p = self.execute_run(power)
                power_value = float(p.get_value(common_pattern))
                self.assertLessEqual(ErrorCode.GPUTCH04, "oam power", power_value, oam_sensor_cfg["max_power"])
                self.assertGreaterEqual(ErrorCode.GPUTCH04, "oam power", power_value, oam_sensor_cfg["min_power"])

                # oam 电压
                cmd_getVoltage = 'ppudbg --monitor power --time 1 --device {} '.format(n) + "| awk '{print $8}'"
                p = self.execute_run(cmd_getVoltage)
                valt_value = float(p.get_value(common_pattern))
                self.assertLessEqual(ErrorCode.FFFFFFFF, "oam voltage", valt_value, oam_sensor_cfg["max_valt"])
                self.assertGreaterEqual(ErrorCode.FFFFFFFF, "oam voltage", valt_value, oam_sensor_cfg["min_valt"])

                # oam 电流
                cmd_getElectric = 'ppudbg --monitor power --time 1 --device {} '.format(n) + "| awk '{print $11}'"
                p = self.execute_run(cmd_getElectric)
                elec_value = float(p.get_value(common_pattern))
                self.assertLessEqual(ErrorCode.FFFFFFFF, "oam electric", elec_value, oam_sensor_cfg["max_elec"])
                self.assertGreaterEqual(ErrorCode.FFFFFFFF, "oam electric", elec_value, oam_sensor_cfg["min_elec"])


if __name__ == '__main__':
    runner.single_runner(FuncSensorOamCheck)
