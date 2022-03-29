# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncOamI2cDeviceCheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/OAM::Slave I2C device Test
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
from Utils.Utility import power


class FuncOamI2cDeviceCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "oam i2c device"
        self.expect = "This is oam 12c device function check test on the server"

        self.config = [
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": "BMC_01"},
        ]

    def exe(self):
        devices = ["0x01", "0x02", "0x04", "0x08", "0x10", "0x20", "0x40", "0x80"]
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            parser = self.execute_run("/etc/init.d/ipmistack stop")
            ret = parser.check_field("stopping")
            self.assertTrue("exist stopping keyword", ret)

            self.execute_run("i2ctransfer -y 10 w1@0x70 0x00")  # 关闭所有的通道
            for dev in devices:
                self.logger.info(f"===========OAM I2C device[{dev}] I/O expander===========")
                self.execute_run(f"i2ctransfer -y 10 w1@0x70 {dev}")
                p = self.execute_run("i2ctransfer -y 10 w1@0x18 0x00 r1")
                val = p.get_origin_data()
                self.assertEqual(f"oam IO expander", val, "0x8f")
                p = self.execute_run("i2ctransfer -y 10 w1@0x1f 0x00 r1")
                val = p.get_origin_data()
                self.assertEqual(f"oam IO expander", val, "0x8f")
                self.logger.info(f"===========OAM I2C device[{dev}] ADC===========")
                self.execute_run("i2ctransfer -y 10 w3@0x10 0x0b 0x02 0x00")
                self.execute_run("i2ctransfer -y 10 w3@0x10 0x04 0xff 0xff")
                self.execute_run(f"i2ctransfer -y 10 w3@0x10 0x02 0x02 {dev}")
                p = self.execute_run("i2ctransfer -y 10 w1@0x10 0x40 r2")
                val = p.get_value(r"0x(\d)")
                self.assertEqual("ADC read value", int(val), power(int(dev, 16)))

            # self.execute_run("/etc/init.d/ipmistack start")
        return Pass(self)

    def tearDown(self):
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            self.execute_run("/etc/init.d/ipmistack start")
            self.sleep(90)

    def tearError(self):
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            self.execute_run("/etc/init.d/ipmistack start")
            self.sleep(90)


if __name__ == '__main__':
    runner.single_runner(FuncOamI2cDeviceCheck)

