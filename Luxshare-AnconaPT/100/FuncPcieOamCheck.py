# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncPcieOamCheck.py
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/PCIE链路测试/OAM info check
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
from Lib.DataBuffer import StrParser
from Utils.Constant import ErrorCode
from Utils.Init import load_mes_info


class FuncPcieOamCheck(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "pcie oam"
        self.expect = "This is pcie oam function check test on the server"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "PCIE", "key": "Pcie"},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.mes_info["info"]["rk"]},
        ]

    def exe(self):
        pcie_config = self.config["PCIE"]
        oam_config = pcie_config["OAM"]
        shangxing = self.config["cfg"]["JBOG"]["shangxing"]

        if shangxing == 8:
            bdfs = "05:01 06:00 7b:01 7c:00 9f:01 a0:00 c3:01 c4:00"
        else:
            bdfs = "ab:01 ac:00 6f:01 70:00"

        # CPU 8475B 4上行查看CPU RC 和Switch上行带宽误码统计
        # for B in 0000 0001; do for D in ab:01 ac:00 6f:01 70:00; do echo $B:$D.0; grep -A 6 $B:$D.0 lspci_full.log|grep -iE "CESta\:|LnkSta\:"|sort|uniq -c; done;done

        # 8上行cycle 统计RC和SW误码和速率
        # for B in 0000 0001; do for D in 05:01 06:00 7b:01 7c:00 9f:01 a0:00 c3:01 c4:00; do echo $B:$D.0; grep -A 6 $B:$D.0 lspci_full.log| grep -iE "CESta\:|LnkSta\:"|sort|uniq -c;done;done

        cmd_dict = {
            "oam": r"""lspci |grep -i "1ded:6001" |cut -d " " -f1 |xargs -I {} lspci -s {} -vvv |grep -iE '1ded|LnkSta:|CESta'""",
            "pcie": f"""for B in 0000 0001; do for D in {bdfs}; do echo $B:$D.0; lspci -s $B:$D.0 -vvv|grep -iE "CESta\:|LnkSta\:"|sort|uniq -c; done;done"""
        }

        with self.ssh_connect(uut=self.config["UUT"]):
            self.step(1, "get memory info")

            for name, cmd in cmd_dict.items():
                parser = self.execute_run(cmd)

                l = parser.split(r"([0-9a-z]{4}:[0-9a-z]{2}:[0-9a-z]{2}\.[0-9a-z]{1})")
                for data in l:
                    if l and len(data) == 12:
                        device = data
                    elif data:
                        parser = StrParser(data)
                        speed = parser.get_value(r"Speed ([0-9]+GT/s)")
                        width = parser.get_value(r"Width (x[0-9]+)")
                        rst = parser.check_field("downgraded")
                        self.assertEqual(ErrorCode.PETALS01, f"pcie {name} {device} speed", speed, oam_config["Speed"])
                        self.assertEqual(ErrorCode.PETALW01, f"pcie {name} {device} width", width, oam_config["Width"])
                        self.assertFalse(ErrorCode.PETERR03, f"pcie {name} {device} check exist (downgrade) keyword",
                                         rst)


if __name__ == '__main__':
    runner.single_runner(FuncPcieOamCheck)
