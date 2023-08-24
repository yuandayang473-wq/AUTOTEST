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
import re

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
from Utils.Init import InitLoadConfig
from Lib.Error import ErrItemFail
from Utils.Utility import trans_format


class InitHibInputParams(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "init ppu project"
        self.expect = "init ppu project"
        self.mes = MesSocket()
        self.tip = "\033[32m{}\033[0m"
        self.fail_tip = "\033[31m{}\033[0m"
        self.ip = None
        self.sn = None
        self.config = [
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def init_get_params(self):
        #     通过服务器交换机端口获取os的ip
        ip = input(self.tip.format("机头OS IP: "))
        pattern = re.compile(r'(([1-9]?\d|1\d\d|2[0-4]\d|25[0-5])\.){3}([1-9]?\d|1\d\d|2[0-4]\d|25[0-5])')
        result = re.fullmatch(pattern, ip)
        if not result:
            fail_msg = "机头OS IP: " + ip + "格式有误!"
            print(self.fail_tip.format(fail_msg))
            self.fail(fail_msg)

        # 获取sn
        sn = input(self.tip.format("Hib SN: "))
        pattern = r"^\w+$"
        result = re.match(pattern, sn)
        if not result:
            fail_sn_msg = "Hib SN: " + sn + "格式有误!"
            print(self.fail_tip.format(fail_sn_msg))
            self.fail(fail_sn_msg)

        self.ip = ip
        self.sn = sn

    def generate_ip_info(self, head_os_ip):
        data = {}
        UUT = {
            "ip_address": head_os_ip,
            "username": "root",
            "password": '123456'
        }
        path = self.config["InitPath"]
        kingkong_path_zip = os.path.join(path["test_path"], path["kingkong"])
        with self.ssh_connect(uut=UUT):
            # copy kingkong

            self.execute_run(f'''df | grep -iE "{path['source_path']}.*/mnt"''', save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                self.execute_run(f"{path['mount_cmd']}")

            self.execute_run(f"ls {path.get('fru_path')}", save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                #  创建文件加
                self.execute_run(f"mkdir -p {path.get('fru_path')}")

            self.execute_run(f"rm -rf {kingkong_path_zip}")
            self.execute_run(f"cp -rf {path['mount_path']}kingkong/{path['kingkong']} {path.get('test_path')}")

            parser = self.execute_run("ipmitool lan print")
            head_bmc_ip = parser.get_value(r"IP Address[ :]+((?:[0-9]+\.){3}[0-9]+)")

            parser = self.execute_run("ipmitool -b 0x0a -t 0x32 lan print 1")
            tail_bmc_ip = parser.get_value(r"IP Address[ :]+((?:[0-9]+\.){3}[0-9]+)")

        bmc_data = {
            "BMC_01": {
                "ip_address": tail_bmc_ip,
                "username": "sysadmin",
                "password": 'superuser'
            },
            "BMC_02": {
                "ip_address": tail_bmc_ip,
                "username": "taobao",
                "password": '9ijn0okm'
            },
            "BMC_03": {
                "ip_address": head_bmc_ip,
                "username": "sysadmin",
                "password": 'superuser'
            }
        }
        data["UUT"] = UUT
        data["TAIL_ADMIN_BMC"] = bmc_data["BMC_01"]
        data["TAIL_TAOBAO_BMC"] = bmc_data["BMC_02"]
        data["HEAD_BMC"] = bmc_data["BMC_03"]
        return data

    def update_params(self, login_info):
        suite = self.parent
        suite.globals.update(login_info)
        tests = suite.get_tests()
        for test_list in tests.values():
            for test_class in test_list:
                test_class.locals.update(login_info)

    def exe(self):
        #  测试 RK
        self.init_get_params()
        data = self.generate_ip_info(self.ip)
        self.update_params(data)

        self.init_settings()
        success = Pass(self)

        data = self.mes.get_hib_pn(self.sn)
        hib_part_number = data["Results"][0]["PN"]
        if hib_part_number is None:
            self.parent.globals["CaseFailStop"] = "yes"
            return Fail(self, ErrItemFail(f"init params fail, hib {self.sn} info error"))

        suite = self.parent
        from_format = "%Y_%m_%d_%H_%M_%S"
        to_format = "%Y-%m-%d %H:%M:%S"
        struct_time = time.strftime(from_format, time.localtime())
        start_time = trans_format(struct_time, from_format, to_format)

        suite.globals["log_prefix"] = self.sn.strip()
        suite.globals['RK'] = "RK0037030025"
        suite.globals["start_time"] = start_time
        # suite.globals["SN"] = self.sn.strip()
        suite.globals["HIB"] = data

        csv = self.locals['CSV']
        stage = csv[:-4] if csv.endswith(".csv") else csv

        sub_folder = stage + "_" + self.sn + "_" + struct_time
        suite.update_root_logger(sub_folder=sub_folder)

        return success

    def init_settings(self):
        user = {
            "ip_address": "localhost",
            "password": "1",
            "username": "root"
        }

        with self.ssh_connect(uut=user):
            for host in [self.locals["UUT"], self.locals["TAIL_TAOBAO_BMC"]]:
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
    runner.single_runner(InitHibInputParams)
