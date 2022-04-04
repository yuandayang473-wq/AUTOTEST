
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


class EicCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Eic link test"
        self.expect = "This is Eic link test for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "UUT.yaml", "name": "Iperf", "key": "Iperf"},{"file": "BmcDevice.yaml", "name": "JBMC", "key":self.locals["TAIL_TAOBAO_BMC"]},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
        ]

    def exe(self):
        server_num = self.locals["PUT"].split("T")[-1]
        path = self.config["InitPath"]
        server = self.config["cfg"]["JBOG"]
        pcie_nic_config = server["fpga_count"]
        if pcie_nic_config == "NA":
            return Pass(self)
        with self.ssh_connect(uut=self.config["UUT"]):
            mount_path = self.config["InitPath"]['mount_path']
            work_path = self.config["InitPath"]['test_path']
            iperf_rpm_file = self.config["Iperf"]['iperftool']
            iperf_script_file = self.config["Iperf"]['iperfscript']
            self.execute_run(f'''df | grep -iE "{path['source_path']}.*/mnt"''', save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                # self.execute_run("mount -t cifs -o vers=2.0,username=Administrator,password=\`1q,sec=ntlmssp,cache=none,nobrl {path.get('source_path')} /mnt")
                self.execute_run(f"{path['mount_cmd']}")
            self.execute_run(f"ls {path.get('fw_path')}", save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                #  创建文件加
                self.execute_run(f"mkdir -p {path.get('fw_path')}")
            self.execute_run(f"ls {path.get('fru_path')}", save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
            #  创建文件加
                self.execute_run(f"mkdir -p {path.get('fru_path')}")
        # self.execute_run(f"rm -rf {path.get('fw_path')}*")
            # self.execute_run(f"rm -rf {path.get('fru_path')}*")
            cmd = "mkdir /LogFile;mount -t cifs -o vers=2.0,username=share,password=Password@_,sec=ntlmssp,cache=none,nobrl //172.20.0.103/LogFile/Backup/Data /LogFile"
            self.execute_run(cmd, save_exit_code=True, i_exit_code=True)
            self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('eictool')} {path.get('test_path')}")
            self.execute_run(f"cd  {path.get('test_path')}{path.get('eictool')}/02-DevelopKit/01-Package/platform/driver && make clean && make modulesymfile=Module.symvers")
            for i in range(10):
                output = self.execute_run(f"cd  {path.get('test_path')}{path.get('eictool')}/02-DevelopKit/01-Package/platform && ./platform_test.sh mt 10").data
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

