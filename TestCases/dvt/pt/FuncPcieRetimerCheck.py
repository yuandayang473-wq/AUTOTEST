# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncPcieRetimerCheck.py
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/PCIE链路测试/Retimer info check (机头)
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
from Utils.DataBuffer import StrParser


class FuncPcieRetimerCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "pcie oam"
        self.expect = "This is pcie oam function check test on the server"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "PCIE", "key": "Pcie"},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
        ]

    def exe(self):
        server = self.config["cfg"]["SERVER"]
        JBOG = self.config["cfg"]["JBOG"]
        pcie_config = self.config["PCIE"]
        retimer_cfg = pcie_config["Retimer"]
        count = 0

        with self.ssh_connect(uut=self.config["UUT"]):
            if JBOG["shangxing"] == 8:
                # 8 上行
                parser = self.execute_run(
                    "for B in 0000 0001; do for D in 06:00 7c:00 a0:00 c4:00; do echo $B:$D.0;  lspci -s $B:$D.0 -vvv|grep -iE 'CESta\:|LnkSta\:'|sort|uniq -c; done;done")
                key = "host-8"
            elif server["cpu_type"] == "8475B" and JBOG["shangxing"] == 4:
                parser = self.execute_run(
                    "for B in 0000 0001; do for D in ac:00 70:00; do echo $B:$D.0;  lspci -s $B:$D.0 -vvv|grep -iE 'CESta\:|LnkSta\:'|sort|uniq -c; done;done")
                key = "host-4-8475B"
            else:
                parser = self.execute_run(
                    "for B in 0000 0001; do for D in 7c:00 c4:00; do echo $B:$D.0;  lspci -s $B:$D.0 -vvv|grep -iE 'CESta\:|LnkSta\:'|sort|uniq -c; done;done")
                key = "host-4"

            config = retimer_cfg[key]

            l = parser.split(r"([0-9a-z]{4}:[0-9a-z]{2}:[0-9a-z]{2}\.[0-9a-z]{1})")
            for data in l:
                if l and len(data) == 12:
                    device = data
                elif data and "Speed" in data:
                    parser = StrParser(data)
                    speed = parser.get_value(r"Speed ([0-9]+GT/s)")
                    width = parser.get_value(r"Width (x[0-9]+)")
                    rst = parser.check_field("downgraded")
                    self.assertEqual(f"pcie retimer {device} speed", speed, config["Speed"])
                    self.assertEqual(f"pcie retimer {device} width", width, config["Width"])
                    self.assertFalse(f"pcie retimer {device} check exist (downgrade) keyword", rst)
                    count += 1

            self.assertEqual("retimer count", count, server["retimer"])

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(FuncPcieRetimerCheck)

