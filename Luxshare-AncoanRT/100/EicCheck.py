
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


class EicCheck(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "Eic link test"
        self.expect = "This is Eic link test for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
            {"folder": "Luxshare-AncoanRT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"folder": "Luxshare-AncoanRT/100/Config", "file": "UUT.yaml", "name": "Iperf", "key": "Iperf"},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key": "BMC_01"},
            {"folder": "Luxshare-AncoanRT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.mes_info["info"]["rk"]},
        ]

    def exe(self):
        path = self.config["InitPath"]
        server = self.config["cfg"]["JBOG"]
        pcie_nic_config = server["fpga_count"]
        if pcie_nic_config == "NA":
            return Pass(self)
        http_server_url = self.mes_info["info"]["http_server_url"]
        eic_tar = os.path.join(http_server_url, "LuxScript/tools/ancoan/Eic/EIC1.0_platfrom_v.1.1.4.2_230731.tar.gz")
        work_path = os.path.dirname(self.root_path)
        self.os_run.run(f"cd {work_path};wget -t 5 -T 60 -r -np -nH -R index.html {eic_tar}")
        with self.ssh_connect(uut=self.config["UUT"]):     
            self.execute_run(f"tar -xvf {work_path}/LuxScript/tools/ancoan/Eic/EIC1.0_platfrom_v.1.1.4.2_230731.tar.gz -C /root/")
            self.execute_run(f"cd  /root/EIC1.0_platfrom_v.1.1.4.2_230731/02-DevelopKit/01-Package/platform/driver && make clean && make modulesymfile=Module.symvers")
            for i in range(10):
                output = self.execute_run(f"cd  /root/EIC1.0_platfrom_v.1.1.4.2_230731/02-DevelopKit/01-Package/platform && ./platform_test.sh mt 10").data
                rst = re.findall(r'Port check test \[OK\]', output, re.I)
                self.logger.info(f" check network is rst : {rst}")
                if not rst:
                    self.logger.error("please check network is health, if the inspection is completed, please press Enter")
                    input('please check network is health, if the inspection is completed, please press Enter')
                    continue
                self.logger.info(" check network is health pass")
                break
           
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(EicCheck)

