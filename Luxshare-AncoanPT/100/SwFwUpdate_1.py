# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   SwFwUpdate_1.py
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
from Utils.Init import load_mes_info


class SwFwUpdate_1(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "Pcie Switch fw check"
        self.expect = "This is Pcie Switch fw check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "Luxshare-AncoanPT/100/Config","file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "Luxshare-AncoanPT/100/Config","file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"folder": "Luxshare-AncoanPT/100/Config","file": "UUT.yaml", "name": "cfg", "key": self.mes_info["info"]["rk"]},
            {"file": "BmcDevice.yaml", "name": "BMC_HEADER", "key": "BMC_03"},
        ]

    def exe(self):
        path = self.config["InitPath"]
        shangxing = self.config["cfg"]["JBOG"]["shangxing"]
        exp_ver = self.config["FwVsersion"]["switch_ver"][shangxing]
        self.os_ip = self.config["UUT"]["ip_address"]

        def update_switch_fw(ver, index):
            if ver != exp_ver:
                self.invoke_run(f"{path.get('pciesw_tool')}", end_with="connect with :")
                self.invoke_run(f"{index}", end_with="PEX89104 B0> ")
                self.invoke_run(f"dl -f {path['sw_fw'][shangxing]}", end_with=":")
                self.invoke_run("Yes", end_with="PEX89104 B0> ")
                parser = self.invoke_run("quit", end_invoke=True)
                if not re.search(r"Image\s*has\s*been\s*downloaded\s*successfully.", parser.get_origin_data(), re.I):
                    self.fail("Pcie switch fw update fail")
                return 0
            return 1

        with self.ssh_connect(uut=self.config["UUT"]):
            for i in range(1, 5):
                cmd = f"{path['pciesw_tool']} -i {i} cli rev"
                data = self.execute_run(cmd, i_exit_code=True, save_exit_code=True).data
                versions = re.findall("Revision:.*", data, re.I)
                for ver in versions:
                    ver = ver.split(":")[1].strip()
                    if update_switch_fw(ver, i) == 0:
                        break
                self.sleep(3)

        self.platform.put_platform_data(self.config["BMC_HEADER"])


if __name__ == '__main__':
    runner.single_runner(SwFwUpdate_1)

