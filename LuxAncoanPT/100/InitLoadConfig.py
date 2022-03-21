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
        mes = MesSocket(url)
        rk, status = mes.save_mes_info(sn)
        if status != 200:
            setattr(self.parent.options, "FailStop", "yes")
            return Fail(self, Error(ErrorCode.FFFFFFFF, f"init params fail, RK[{rk}] error!"))
        data = {
            "info": {
                "sn": sn,
                "url": url,
                "rk": rk,
                "http_server_url": http_server_url
            }
        }
        JsonLoadConfig(cfg_path_name="", cfg_name="mes_info.json").set_config(data, is_new_file=True)

        PpuInitLoadConfig().load_config(self.get_logger())
        self.init_settings()

    def init_settings(self):
        import paramiko
        for host in [self.config["TAIL_TAOBAO_BMC"]]:
            ip = host["ip_address"]
            user = host["username"]
            password = host["password"]
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
            ssh.connect(ip, username=user, password=password)
            ssh.close()


if __name__ == '__main__':
    runner.single_runner(InitLoadConfig)
