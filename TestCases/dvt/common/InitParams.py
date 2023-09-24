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
import time

from Utils.Utility import trans_format

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
from Lib.Request import MesSocket
from Utils.GlobalConfig import InitLoadConfig
from Lib.Error import ErrItemFail


class InitParams(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "init ppu project"
        self.expect = "init ppu project"
        self.mes = MesSocket()
        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals['UUT']},
            {"file": "BmcDevice.yaml", "name": "TAIL_TAOBAO_BMC", "key": self.locals["TAIL_TAOBAO_BMC"]},
        ]
        self.sn, self.put = InitLoadConfig().load_config(self.locals["PUT"])

    def exe(self):
        #  测试 RK
        self.init_settings()
        success = Pass(self)
        rk, status = self.mes.save_mes_info(self.sn)
        if status != 200:
            setattr(self.parent.options, "FailStop", "yes")
            return Fail(self, ErrItemFail(f"init params fail, RK[{rk}] error!"))

        suite = self.parent
        from_format = "%Y_%m_%d_%H_%M_%S"
        to_format = "%Y-%m-%d %H:%M:%S"
        struct_time = time.strftime(from_format, time.localtime())
        start_time = trans_format(struct_time, from_format, to_format)

        suite.globals["log_prefix"] = self.put.strip()
        suite.globals['RK'] = rk
        suite.globals["start_time"] = start_time
        suite.globals["SN"] = self.sn.strip()

        csv = self.locals['CSV']
        stage = csv[:-4] if csv.endswith(".csv") else csv

        sub_folder = self.locals["PUT"] + "_" + stage + "_" + self.sn + "_" + struct_time
        suite.update_root_logger(sub_folder=sub_folder)

        return success

    def init_settings(self):
        user = {
            "ip_address": "localhost",
            "password": "123456",
            "username": "root"
        }

        with self.ssh_connect(uut=user):
            for host in [self.config["UUT"], self.config["TAIL_TAOBAO_BMC"]]:
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
    runner.single_runner(InitParams)
