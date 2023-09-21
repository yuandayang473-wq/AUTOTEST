# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   SwFwUpdate.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re

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


class SwFwUpdate(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "Pcie Switch fw check"
        self.expect = "This is Pcie Switch fw check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.mes_info["info"]["rk"]},
        ]

    def exe(self):
        path = self.config["InitPath"]
        shangxing = self.config["cfg"]["JBOG"]["shangxing"]

        exp_ver = "2:3" if shangxing == 8 else "2:2"
        self.execute_run("chmod -R 777 /pscuut/9001/work/LuxScript/")
        def update_switch_fw(ver,index):
            with self.ssh_connect(uut=self.config["UUT"]):
                if ver != exp_ver:
                    self.invoke_run(f"{path.get('pciesw_tool')}", end_with="connect with :")
                    self.invoke_run(f"{index+1}", end_with="PEX89104 B0> ")
                    self.invoke_run(f"dl -f {path['sw_fw'][shangxing]}", end_with=":")
                    self.invoke_run("Yes", end_with="PEX89104 B0> ")
                    parser = self.invoke_run("quit", end_invoke=True)
                    if not re.search(r"Image\s*has\s*been\s*downloaded\s*successfully.", parser.get_origin_data(), re.I):
                        self.fail(ErrorCode.FWTUP00D, "Pcie switch fw update fail")

        with self.ssh_connect(uut=self.config["UUT"]):
            self.invoke_run(f"{path['pciesw_tool']}", end_with="connect with :")

            for i in range(1, 4):
                self.invoke_run(f"{i}", end_with="PEX89104 B0>")
                self.invoke_run("cli showmfg", end_with="PEX89104 B0>")
                self.invoke_run("list", end_with="connect with :")

            self.invoke_run("4", end_with="PEX89104 B0> ")
            self.invoke_run("cli showmfg", end_with="PEX89104 B0>")

            parser = self.invoke_run("quit", end_invoke=True)
            versions = parser.filter_list(r"Associated FW ver[: ]+\d:\d:(\d:\d)")
        
            if len(versions) == 0:
                self.fail(ErrorCode.FFFFFFFF, "Get pcie switch fw version fail")

        for index,ver in enumerate(versions):
            update_switch_fw(ver, index)
            
        


if __name__ == '__main__':
    runner.single_runner(SwFwUpdate)

