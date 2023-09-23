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


class InitTestEnvironment(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "Init test environment write"
        self.expect = "This is Init test environment write."

        self.config = [
            {"folder": "Luxshare-AncoanRT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "tools/ancoan/rpm"}
        ]

    def exe(self):
        init_path = self.config["InitPath"]
        http_server_url = self.mes_info["info"]["http_server_url"]
        _fw = os.path.join(http_server_url, "LuxScript/tools/ancoan/fw/")
        _fru = os.path.join(http_server_url, "LuxScript/tools/ancoan/fru/")

        ali_driver = os.path.join(http_server_url, f"LuxScript/tools/ancoan/rpm/{init_path['aliaom_driver'].split('/')[-1]}")
        sshpass_driver = os.path.join(http_server_url, "LuxScript/tools/ancoan/rpm/sshpass-1.09-4.el8.x86_64.rpm")
        path = os.path.dirname(self.root_path)
        self.os_run.run(f"cd {path};wget -t 5 -T 60 -r -np -nH -R index.html {_fw}")
        self.os_run.run(f"cd {path};wget -t 5 -T 60 -r -np -nH -R index.html {_fru}")
        self.os_run.run(f"cd {path};wget -t 5 -T 60 -r -np -nH -R index.html {ali_driver}")
        self.os_run.run(f"cd {path};wget -t 5 -T 60 -r -np -nH -R index.html {sshpass_driver}")

        self.os_run.run(f"rpm -ivh --nodeps --force {init_path['aliaom_driver']}")
        self.os_run.run(f"rpm -ivh --nodeps --force {init_path['sshpass']}")
        self.os_run.run(f"chmod +777 {self.root_path}/tools/ancoan")


if __name__ == '__main__':
    runner.single_runner(InitTestEnvironment)
