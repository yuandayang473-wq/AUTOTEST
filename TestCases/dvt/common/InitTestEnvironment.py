# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   InitTestEnvironment.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
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


class InitTestEnvironment(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Init test environment write"
        self.expect = "This is Init test environment write."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals['UUT']},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        path = self.config["InitPath"]
        user = {
            "ip_address": "localhost",
            "password": "1",
            "username": "root"
        }
        with self.ssh_connect(uut=user):
            # self.execute_run(f'''[[ `df | grep -iE "//192.2.19.51/share.*/mnt"` != '' ]] || mount -t cifs -o username=Administrator,password=\`1q {path.get('source_path')} /mnt ''',i_exit_code=True)
            # self.execute_run(f"[ ! -d {path.get('fw_path')} ] && mkdir -p {path.get('fw_path')}",i_exit_code=True)
            # self.execute_run(f"rm -rf {path.get('fw_path')}*",i_exit_code=True)
            # self.execute_run(f"\cp -rf {path['fw_source_path']} {path.get('fw_path')}",i_exit_code=True)

            self.execute_run(f'''df | grep -iE "{path['source_path']}.*/mnt"''', save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                self.execute_run(f"{path['mount_cmd']}")

            self.execute_run(f"ls {path.get('fw_path')}", save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                #  创建文件加
                self.execute_run(f"mkdir -p {path.get('fw_path')}")
                self.execute_run(f"cp -rf {path['fw_source_path']} {path.get('fw_path')}")

            # # 存在，删除文件夹内容
            # self.execute_run(f"rm -rf {path.get('fw_path')}*")

        with self.ssh_connect(uut=self.config["UUT"]):
            # self.execute_run(
            #     f'''[[ `df | grep -iE "//192.2.19.51/share.*/mnt"` != '' ]] || mount -t cifs -o vers=2.0,username=Administrator,password=\`1q,sec=ntlmssp,cache=none,nobrl {path.get('source_path')} /mnt ''',
            #     i_exit_code=True)
            # self.execute_run(f"rpm -ivh {path.get('mount_path')}sshpass-1.09-4.el8.x86_64.rpm", i_exit_code=True)
            # self.execute_run(f"[ ! -d {path.get('fru_path')} ] && mkdir -p {path.get('fru_path')}")
            # self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('aliaom_driver')} {path.get('test_path')}")
            # self.execute_run(f"rpm -ivh --nodeps --force {path.get('test_path')}{path.get('aliaom_driver')}")
            # self.execute_run(f"rpm -ivh {path.get('mount_path')}mft-4.20.1-14.x86_64.rpm", i_exit_code=True)
            # self.execute_run(f"rm -rf {path.get('fru_path')}/*")
            # self.execute_run(f"cp -rf /mnt/fru/* {path.get('fru_path')}")
            # self.execute_run(f"[ ! -d {path.get('fw_path')} ] && mkdir -p {path.get('fw_path')}", i_exit_code=True)
            # self.execute_run(f"rm -rf {path.get('fw_path')}/*")
            # self.execute_run(f"\cp -rf {path['fw_source_path']} {path.get('fw_path')}")
            # self.execute_run(f"cp -rf {path['mount_path']}kingkong/{path['kingkong']} {path.get('test_path')}")
            # self.execute_run("chmod -R 777 /opt/Alioam/")

            self.execute_run(f'''df | grep -iE "{path['source_path']}.*/mnt"''', save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                # self.execute_run("mount -t cifs -o vers=2.0,username=Administrator,password=\`1q,sec=ntlmssp,cache=none,nobrl {path.get('source_path')} /mnt")
                self.execute_run(f"{path['mount_cmd']}")

            # self.execute_run(f"[ ! -d {path.get('fw_path')} ] && mkdir -p {path.get('fw_path')}", i_exit_code=True)
            self.execute_run(f"ls {path.get('fw_path')}", save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                #  创建文件加
                self.execute_run(f"mkdir -p {path.get('fw_path')}")

            self.execute_run(f"ls {path.get('fru_path')}", save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                #  创建文件加
                self.execute_run(f"mkdir -p {path.get('fru_path')}")

            self.execute_run(f"rm -rf {path.get('fw_path')}*")
            self.execute_run(f"rm -rf {path.get('fru_path')}*")

            self.execute_run(f"cp -rf /mnt/fru/* {path.get('fru_path')}")
            self.execute_run(f"cp -rf {path['fw_source_path']} {path.get('fw_path')}")
            #self.execute_run(f"cp -rf {path['mount_path']}kingkong/{path['kingkong']} {path.get('test_path')}")
            self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('aliaom_driver')} {path.get('test_path')}")
            
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('test_path')}{path.get('aliaom_driver')}")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}mft-4.20.1-14.x86_64.rpm")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}sshpass-1.09-4.el8.x86_64.rpm")

            self.execute_run("chmod -R 777 /opt/Alioam/")
            
        return Pass(self)


if __name__ == '__main__':
    runner.batch_runner(InitTestEnvironment)
