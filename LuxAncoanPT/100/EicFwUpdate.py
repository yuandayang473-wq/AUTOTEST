
# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Harvey
@Software:   TestCase
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import re
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

from Lib.Result import Pass, Fail
from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Init import load_mes_info
from Lib.Request import MesSocket

class EicFwUpdate(TempItem):
    
    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "Eic link test"
        self.expect = "This is Eic link test for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "UUT.yaml", "name": "Iperf", "key": "Iperf"},{"file": "BmcDevice.yaml", "name": "JBMC", "key":self.locals["TAIL_TAOBAO_BMC"]},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def exe(self):
        server_num = self.locals["PUT"].split("T")[-1]
        path = self.config["InitPath"]
        server = self.config["cfg"]["JBOG"]
        pcie_nic_config = server["fpga_count"]
        eic_ver = self.config["FwVsersion"]["eicfw_ver"]
        if pcie_nic_config == "NA":
            return Pass(self)
        with self.ssh_connect(uut=self.config["UUT"]):
            self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('eictool')} {path.get('test_path')}")
            self.execute_run(f"cd  {path.get('test_path')}{path.get('eictool')}/02-DevelopKit/01-Package/platform/driver && make clean && make modulesymfile=Module.symvers", i_exit_code=True)
            self.execute_run(f"cd  {path.get('test_path')}{path.get('eictool')}/02-DevelopKit/01-Package/platform/ && ./platform_test.sh mt 7 -a work -r ")
            output = self.execute_run(f"cd  {path.get('test_path')}{path.get('eictool')}/02-DevelopKit/01-Package/platform && ./platform_test.sh mt 0").data
            rst = re.findall(r'fpga version.*', output, re.I)
            self.logger.info(f" fpga version: {rst}")
            if len(rst) != pcie_nic_config:
                return Fail(self)
            for ver in rst:
                ver = ver.split(":")[1].strip()
                if ver != eic_ver:
                    self.execute_run(f"cd  {path.get('test_path')}{path.get('eictool')}/02-DevelopKit/01-Package/platform/ && ./platform_test.sh mt 7 -a work -f files/{path.get('eicupdatefile')} ")
                    break
            self.execute_run(f"cd  {path.get('test_path')}{path.get('eictool')}/02-DevelopKit/01-Package/platform/ && ./platform_test.sh mt 7 -a work -r ")
            
           
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(EicFwUpdate)

