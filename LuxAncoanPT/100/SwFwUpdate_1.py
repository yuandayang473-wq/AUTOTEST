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

            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "BmcDevice.yaml", "name": "BMC_HEADER", "key": self.locals["HEAD_BMC"]},
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

        header_bmc_ip = self.config["BMC_HEADER"]["ip_address"]
        with self.ssh_connect(uut=self.config["UUT"]):
            self.logger.info("server reset ")
            self.execute_run(f"ipmitool -I lanplus -H {header_bmc_ip} -U taobao -P 9ijn0okm power reset")
            self.ping_pang(self.os_ip, sleep_time=60, mode="on")



        with self.ssh_connect(uut=self.config["UUT"]):
            ath = self.config["InitPath"]
            cmd = "mkdir /LogFile;mount -t cifs -o vers=2.0,username=share,password=Password@_,sec=ntlmssp,cache=none,nobrl //172.20.0.103/LogFile/Backup/Data /LogFile"
            self.execute_run(cmd, i_exit_code=True, save_exit_code=True)
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
            self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('aliaom_driver')} {path.get('test_path')}")
            self.execute_run(f"cp -rf {path['fw_source_path']} {path.get('fw_path')}")
            self.execute_run(f"cp -rf {path['mount_path']}kingkong/{path['kingkong']} {path.get('test_path')}")
            self.execute_run(f"cp -rf /mnt/fru/* {path.get('fru_path')}")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('test_path')}{path.get('aliaom_driver')}")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}mft-4.20.1-14.x86_64.rpm")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}sshpass-1.09-4.el8.x86_64.rpm")
            self.execute_run("chmod -R 777 /opt/Alioam/")

            for i in range(1, 5):
                cmd = f"{path['pciesw_tool']} -i {i} cli rev"
                data = self.execute_run(cmd, i_exit_code=True, save_exit_code=True).data
                versions = re.findall("Revision:.*", data, re.I)
                for ver in versions:
                    ver = ver.split(":")[1].strip()
                    if update_switch_fw(ver, i) == 0:
                        break
                time.sleep(3)

        with self.ssh_connect(uut=self.config["UUT"]):
            for i in range(1, 5):
                cmd = f"{path['pciesw_tool']} -i {i} cli rev"
                data = self.execute_run(cmd, i_exit_code=True, save_exit_code=True).data
                versions = re.findall("Revision:.*", data, re.I)
                for ver in versions:
                    ver = ver.split(":")[1].strip()
                    self.assertEqual(f"SwFwcheck ", ver, exp_ver)
                time.sleep(3)
            
        


if __name__ == '__main__':
    runner.single_runner(SwFwUpdate)

