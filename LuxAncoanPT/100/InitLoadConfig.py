# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   InitParams.py
@Time    :   2023/5/8
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   初始RK,必须要的参数
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
from Utils.Init import PpuInitLoadConfig


class InitLoadConfig(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "init ppu"
        self.expect = "load project info"

    def exe(self):
        PpuInitLoadConfig().load_config(self.get_logger())
        self.init_settings()

    def init_settings(self):
        user = {
            "ip_address": "localhost",
            "password": "123456",
            "username": "root"
        }

        self.config = [
            {"file": "BmcDevice.yaml", "name": "TAIL_TAOBAO_BMC", "key": "BMC_02"},
        ]
        with self.ssh_connect(uut=user):
            for host in [self.config["TAIL_TAOBAO_BMC"]]:
                ip = host["ip_address"]
                user = host["username"]
                password = host["password"]
                self.execute_run(f"cat /root/.ssh/known_hosts | grep -i '{ip}'", save_exit_code=True)
                if self.ssh.get_exit_code() == 0:
                    self.execute_run(f"sed -i '/{ip}/d' /root/.ssh/known_hosts", i_exit_code=True)

                self.sleep(3)
                self.invoke_run(f"ssh {user}@{ip}", end_with="yes/no")
                self.invoke_run("yes", end_with="password")
                self.invoke_run(f"{password}", end_with="# |~ |$")
                self.invoke_run("exit", end_invoke=True)
                self.sleep(3)


if __name__ == '__main__':
    runner.single_runner(InitLoadConfig)
