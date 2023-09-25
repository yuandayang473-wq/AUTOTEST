
# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Software:   TestCase
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import re
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

from Lib.Result import Pass, Fail
from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Init import load_mes_info


class EicFwUpdate(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "Eic link test"
        self.expect = "This is Eic link test for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
            {"folder": "LuxAncoanPT/100/Config","file": "UUT.yaml", "name": "Eic", "key": "tools/ancoan/Eic"},
            {"folder": "LuxAncoanPT/100/Config","file": "UUT.yaml", "name": "Eic_info", "key": "tools.ancoan.Eic"},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key": "BMC_02"},
            {"folder": "LuxAncoanPT/100/Config","file": "UUT.yaml", "name": "cfg", "key": self.mes_info["info"]["rk"]},
            {"folder": "LuxAncoanPT/100/Config","file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def init_eic_env(self):
        http_server_url = self.mes_info["info"]["http_server_url"]
        _eic = os.path.join(http_server_url, "LuxScript/tools/ancoan/Eic/")
        path = os.path.dirname(self.root_path)
        self.os_run.run(f"cd {path};wget -t 5 -T 60 -r -np -nH -R index.html {_eic}")

        # 解压
        eic_cfg = self.config["Eic"]
        self.os_run.run(f"tar -zxvf {eic_cfg['tar']}")

    def exe(self):

        server = self.config["cfg"]["JBOG"]
        pcie_nic_config = server["fpga_count"]
        eic_ver = self.config["FwVsersion"]["eicfw_ver"]
        if pcie_nic_config == "NA":
            return Pass(self)

        self.init_eic_env()

        name = self.config["Eic_info"]["name"]
        eicupdatefile = self.config["Eic_info"]["eicupdatefile"]

        self.os_run.run(f"cd  {name}/02-DevelopKit/01-Package/platform/driver && make clean && make modulesymfile=Module.symvers", i_exit_code=True)
        self.os_run.run(f"cd  {name}/02-DevelopKit/01-Package/platform/ && ./platform_test.sh mt 7 -a work -r ")
        output = self.os_run.run(f"cd  {name}/02-DevelopKit/01-Package/platform && ./platform_test.sh mt 0").data
        rst = re.findall(r'fpga version.*', output, re.I)
        self.logger.info(f" fpga version: {rst}")
        if len(rst) != pcie_nic_config:
            return Fail(self)
        for ver in rst:
            ver = ver.split(":")[1].strip()
            if ver != eic_ver:
                self.os_run(f"cd  {name}/02-DevelopKit/01-Package/platform/ && ./platform_test.sh mt 7 -a work -f files/{eicupdatefile} ")
                break
        self.os_run(f"cd  {name}/02-DevelopKit/01-Package/platform/ && ./platform_test.sh mt 7 -a work -r ")


if __name__ == '__main__':
    runner.single_runner(EicFwUpdate)

