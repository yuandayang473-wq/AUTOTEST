# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   BiosFwUpdate.py
@Time    :   2022/2/1
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re
import time
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


class BiosFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "bios fw check"
        self.expect = "This is bios fw update for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "BmcDevice.yaml", "name": "HEADER_TAIL", "key": "BMC_03"},
            {"folder": "LuxAncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
        ]

    def exe(self):
        path = self.config["InitPath"]
        header_bmc_ip = self.config["HEADER_TAIL"]["ip_address"]
        target_bios_ver = self.config["FwVsersion"]["bios_ver"]
        with self.ssh_connect(uut=self.config["UUT"]):
            parser = self.execute_run("dmidecode -t bios | grep -i version | awk '{print $2}'")
            if parser.get_origin_data() != target_bios_ver:
                parser = self.execute_run("chmod +x /opt/Alioam/fw/bios/*")
                parser = self.execute_run(f"{path.get('bios_Script')} {header_bmc_ip} taobao 9ijn0okm {path.get('bios_fw')} 1")
                if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                    self.logger.info("Header bios flash bure fail")
                    self.fail(ErrorCode.FFFFFFFF, "Header bios flash bure fail")
                self.execute_run("reboot",  i_exit_code=True)
                time.sleep(400)
        with self.ssh_connect(uut=self.config["UUT"]):
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
            self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('aliaom_driver')} {path.get('test_path')}")
            self.execute_run(f"cp -rf {path['fw_source_path']} {path.get('fw_path')}")
            self.execute_run(f"cp -rf {path['mount_path']}kingkong/{path['kingkong']} {path.get('test_path')}")
            self.execute_run(f"cp -rf /mnt/fru/* {path.get('fru_path')}")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('test_path')}{path.get('aliaom_driver')}")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}mft-4.20.1-14.x86_64.rpm")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}sshpass-1.09-4.el8.x86_64.rpm")
            self.execute_run("chmod -R 777 /opt/Alioam/")
        


if __name__ == '__main__':
    runner.single_runner(BiosFwUpdate)

