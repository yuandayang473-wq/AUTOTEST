# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   HealthCheck.py
@Time    :   2023/5/9
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   健康检查
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
from Utils.Constant import ErrorCode


class HWQC(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "hwqc"
        self.expect = "This is hwqc test"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key": "BMC_02"},
            {"folder": "Luxshare-AnconaRT1/100/Config", "file": "UUT.yaml", "name": "rpm", "key": "tools/ancoan/rpm"},
            {"folder": "Luxshare-AnconaRT1/100/Config", "file": "UUT.yaml", "name": "rpm_info", "key": "tools.ancoan.rpm"},
            {"folder": "Luxshare-AnconaRT1/100/Config", "file": "UUT.yaml", "name": "hwqc", "key": "tools/ancoan/HWQC"},
        ]

    @load_mes_info
    def init_env(self):
        hwqc_target_path = os.path.join("/root", "HWQC")

        http_server_url = self.mes_info["info"]["http_server_url"]
        _hwqc = os.path.join(http_server_url, "LuxScript/tools/ancoan/HWQC/")
        # ali_driver = os.path.join(http_server_url,f"LuxScript/tools/ancoan/rpm/{self.config['rpm_info']['aliaom_driver']}")
        alippu_driver = os.path.join(http_server_url,f"LuxScript/tools/ancoan/rpm/{self.config['rpm_info']['alippu_driver']}")
        self.wget(_hwqc)
        self.wget(alippu_driver)

        rpm = self.config["rpm"]
        hwqc = self.config["hwqc"]
        # 安装driver
        # self.os_run.run(f"rpm -ivh --nodeps --force {rpm['aliaom_driver']}")
        self.os_run.run(f"rpm -ivh --nodeps --force {rpm['alippu_driver']}")
        self.os_run.run(f"rpm -ivh --nodeps --force {hwqc['pub_rpm']}")

        # 解压zip 文件
        self.os_run.run(f"rm -rf {hwqc_target_path}")

        self.os_run.run(f"unzip -d {hwqc_target_path} {hwqc['hwqc_zip']}")
        self.os_run.run(f"tar -xvf {hwqc['alibabacloud_tar']} -C {hwqc_target_path}")

        cfg_path = os.path.join(hwqc_target_path, "hwqc_factory/cfg")
        baseline_path = os.path.join(cfg_path, "baseline")
        self.os_run.run(f"mkdir -p {baseline_path}")

        alibabacloud_path = os.path.join(hwqc_target_path, "alibabacloud")
        self.os_run.run(f"cp -r {alibabacloud_path} {baseline_path}")
        disk_py_path = os.path.join(hwqc_target_path, "disk.py")
        disk_pyc_path = os.path.join(cfg_path, "disk.pyc")
        mem_py_path = os.path.join(hwqc_target_path, "mem.py")
        mem_pyc_path = os.path.join(cfg_path, "mem.pyc")
        self.os_run.run(f"cp {disk_py_path} {cfg_path}")
        self.os_run.run(f"cp {mem_py_path} {cfg_path}")

        self.os_run.run(f"rm -rf {disk_pyc_path}")
        self.os_run.run(f"rm -rf {mem_pyc_path}")

        raid_type_path = os.path.join(hwqc_target_path, "raid_type.yaml")
        baseline_cfg_path = os.path.join(hwqc_target_path, "baseline.cfg")
        self.os_run.run(f"cp {raid_type_path} {baseline_path}")
        self.os_run.run(f"cp {baseline_cfg_path} {baseline_path}")

    def copy_log(self, log_path):
        logs = os.path.join(log_path, "hwqc.*.log")
        reports = os.path.join(log_path, "hwqc.*.report")
        self.os_run.run(f"mv {logs} {self.CUSTOM_LOG_PATH}")
        self.os_run.run(f"mv {reports} {self.CUSTOM_LOG_PATH}")

    def exe(self):
        hwqc_factory_path = os.path.join("/root", "HWQC", "hwqc_factory")
        hwqc_pyc_path = os.path.join(hwqc_factory_path, "hwqc.pyc")
        tail_bmc_ip = self.config["JBMC"]["ip_address"]

        self.init_env()

        parser = self.os_run.run("ipmitool fru list")
        chassis_part_number = parser.get_value(r"Chassis Part Number[: ]+(\w+)\.\w+")

        self.os_run.run("rmmod -f usb-storage", i_exit_code=True)
        self.os_run.run("rmmod -f ahci")
        self.os_run.run("rmmod -f mpt3sas")
        self.os_run.run("modprobe ahci")
        self.os_run.run("modprobe mpt3sas")

        parser = self.os_run.run(f"python {hwqc_pyc_path} -a {chassis_part_number} -m alibabacloud base",i_exit_code=True)

        result = parser.check_field(r"base[: ]+OK")
        if not result:
            self.copy_log("/tmp")
            self.fail(ErrorCode.FFFFFFFF, "head HWQC fail")

        parser = self.os_run.run(f"ipmitool -I lanplus -H {tail_bmc_ip} -U admin -P admin fru list")
        chassis_part_number = parser.get_value(r"Chassis Part Number[: ]+(\w+)\.\w+")

        parser = self.os_run.run(
            f"python {hwqc_pyc_path} -H {tail_bmc_ip} -U admin -P admin -a {chassis_part_number} -m alibabacloud all",
            i_exit_code=True)
        result = parser.check_field(r"base[: ]+OK")

        self.copy_log("/tmp")

        if not result:
            self.fail(ErrorCode.FFFFFFFF, "tail HWQC fail")


if __name__ == '__main__':
    runner.single_runner(HWQC)
