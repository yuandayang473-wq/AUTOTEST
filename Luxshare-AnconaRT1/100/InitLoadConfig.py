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
from Lib.Config import JsonLoadConfig
from Lib.Request import MesSocket
from Lib.Result import Fail
from Lib.Error import Error
from Utils.Constant import ErrorCode
from Utils.Init import PpuInitLoadConfig


class InitLoadConfig(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "init ppu"
        self.expect = "load project info"

    def exe(self):

        cfg = JsonLoadConfig(cfg_path_name="", cfg_name="jobcontext.json").get_config()
        sn = cfg["unitData"]["name"].strip()
        url = cfg["flowdata"]["tcs_data_url"].strip()
        http_server_url = cfg["flowdata"]["http_server_url"].strip()
        mes = MesSocket(url, sn)
        rk, status = mes.save_mes_info(sn)
        if status != 200:
            setattr(self.parent.options, "FailStop", "yes")
            return Fail(self, Error(ErrorCode.FFFFFFFF, f"init params fail, RK[{rk}] error!"))
        data = {
            "info": {
                "sn": sn,
                "url": url,
                "rk": rk,
                "http_server_url": http_server_url,
            }
        }
        JsonLoadConfig(cfg_path_name="", cfg_name="mes_info.json").dump_config(data, is_new_file=True)

        PpuInitLoadConfig().load_config(self.get_logger())
        # bmc_data = PpuInitLoadConfig().load_config(self.get_logger())
        # self.init_settings(uut_data, bmc_data)

    def init_settings(self, bmc_data):
        import paramiko
        for host in [bmc_data["BMC_02"]]:
            ip = host["ip_address"]
            user = host["username"]
            password = host["password"]
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
            ssh.connect(ip, username=user, password=password)
            ssh.close()

    def init_settings_1(self, bmc_data):
        user = {
            "ip_address": "localhost",
            "password": "1",
            "username": "root"
        }

        with self.ssh_connect(uut=user):
            for host in [bmc_data["BMC_02"]]:
                ip = host["ip_address"]
                user = host["username"]
                password = host["password"]
                self.execute_run(f"cat /root/.ssh/known_hosts | grep -i '{ip}'", save_exit_code=True)
                if self.ssh.get_exit_code() == 0:
                    self.execute_run(f"sed -i '/{ip}/d' /root/.ssh/known_hosts", i_exit_code=True)

                self.sleep(3)
                # parser = self.invoke_run(f"ssh {user}@{ip}", end_with="yes/no|password", end_invoke=True)
                # ret = parser.check_field(r"yes/no")
                # if ret:
                #     self.invoke_run(f"ssh {user}@{ip}", end_with="yes/no")
                #     self.invoke_run("yes", end_with="password")
                self.invoke_run(f"ssh {user}@{ip}", end_with="yes/no")
                self.invoke_run("yes", end_with="password")
                self.invoke_run(f"{password}", end_with="# |~ |$")
                self.invoke_run("exit", end_invoke=True)
                self.sleep(3)


if __name__ == '__main__':
    runner.single_runner(InitLoadConfig)
