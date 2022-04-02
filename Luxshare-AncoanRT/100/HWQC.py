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


class HWQC(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "hwqc"
        self.expect = "This is hwqc test"

        #
        # UUT = {
        #     "ip_address": "192.2.37.184",
        #     "username": "root",
        #     "password": '123456'
        # }

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key": self.locals["TAIL_TAOBAO_BMC"]},
            # {"file": "Device.yaml", "name": "UUT", "key": UUT},
            {"file": "UUT.yaml", "name": "path", "key": "InitPath"},
        ]

    def init_env(self):
        path = self.config["path"]

        mount_path = path.get('mount_path')
        test_path = path.get('test_path')
        alidriver_source_rpm = os.path.join(mount_path, path.get('aliaom_driver'))
        alidriver_target_rpm = os.path.join(test_path, path.get('aliaom_driver'))
        alippudriver_source_rpm = os.path.join(mount_path, path.get('alippu_driver'))
        alippudriver_target_rpm = os.path.join(test_path, path.get('alippu_driver'))
        hwqc_source_path = os.path.join(mount_path, "HWQC")
        hwqc_target_path = os.path.join("/root", "HWQC")

        hwqc_pub_rpm = os.path.join(hwqc_target_path, "pub_*.rpm")
        hwqc_alibaba_tar = os.path.join(hwqc_target_path, "alibabacloud*.tar")
        hwqc_factory_zip = os.path.join(hwqc_target_path, "hwqc_*.zip")

        # mount
        self.execute_run(f'''df | grep -iE "{path['source_path']}.*/mnt"''', save_exit_code=True, desc="is mount /mnt")
        if self.ssh.get_exit_code() != 0:
            self.execute_run(f"{path['mount_cmd']}")

        self.execute_run(f"rm -rf {hwqc_target_path}")
        self.execute_run(f"cp -rf {hwqc_source_path} /root")

        self.execute_run(f"[ ! -d {test_path} ] && mkdir -p {test_path}", i_exit_code=True)
        # cp file
        self.execute_run(f"\cp {alidriver_source_rpm} {test_path}")
        self.execute_run(f"\cp {alippudriver_source_rpm} {test_path}")

        # rpm 安装driver
        self.execute_run(f"rpm -ivh --nodeps --force {alidriver_target_rpm}")
        self.execute_run(f"rpm -ivh --nodeps --force {hwqc_pub_rpm}")
        self.execute_run(f"rpm -ivh --nodeps --force {alippudriver_target_rpm}")

        self.execute_run(f"unzip -d {hwqc_target_path} {hwqc_factory_zip}")
        self.execute_run(f"tar -xvf {hwqc_alibaba_tar} -C {hwqc_target_path}")

        cfg_path = os.path.join(hwqc_target_path, "hwqc_factory/cfg")
        baseline_path = os.path.join(cfg_path, "baseline")
        self.execute_run(f"mkdir -p {baseline_path}")

        alibabacloud_path = os.path.join(hwqc_target_path, "alibabacloud")
        self.execute_run(f"cp -r {alibabacloud_path} {baseline_path}")
        disk_py_path = os.path.join(hwqc_target_path, "disk.py")
        disk_pyc_path = os.path.join(cfg_path, "disk.pyc")
        mem_py_path = os.path.join(hwqc_target_path, "mem.py")
        mem_pyc_path = os.path.join(cfg_path, "mem.pyc")
        self.execute_run(f"cp {disk_py_path} {cfg_path}")
        self.execute_run(f"cp {mem_py_path} {cfg_path}")

        self.execute_run(f"rm -rf {disk_pyc_path}")
        self.execute_run(f"rm -rf {mem_pyc_path}")

        raid_type_path = os.path.join(hwqc_target_path, "raid_type.yaml")
        baseline_cfg_path = os.path.join(hwqc_target_path, "baseline.cfg")
        self.execute_run(f"cp {raid_type_path} {baseline_path}")
        self.execute_run(f"cp {baseline_cfg_path} {baseline_path}")

    # def copy_log(self, succes_path, fail_path):
    def copy_log(self, log_path):
        path = self.config["path"]
        mount_path = path.get('mount_path')
        sn = self.parent.globals["SN"]
        hwqc_log = os.path.join(mount_path, "HWQC_Log")
        sn_path = os.path.join("/root", sn)
        # sn_path_zip = os.path.join(f"{sn}.zip")
        # sn_path_zip = f"{sn}.zip"
        self.execute_run(f"mkdir -p {sn_path}")
        # for log_path in [succes_path, fail_path]:
        #     if log_path:
        logs = os.path.join(log_path, "hwqc.*.log")
        reports = os.path.join(log_path, "hwqc.*.report")
        self.execute_run(f"mv {logs} {sn_path}")
        self.execute_run(f"mv {reports} {sn_path}")

        # self.execute_run(f"zip -r {sn_path_zip} {sn}")
        self.execute_run(f"rm -rf {hwqc_log}/{sn}")
        self.execute_run(f"mv {sn_path} {hwqc_log}")

    def exe(self):
        hwqc_factory_path = os.path.join("/root", "HWQC", "hwqc_factory")
        hwqc_pyc_path = os.path.join(hwqc_factory_path, "hwqc.pyc")
        tail_bmc_ip = self.config["JBMC"]["ip_address"]
        success_log_path = None
        fail_log_path = None
        with self.ssh_connect(uut=self.config["UUT"]):
            self.init_env()

            parser = self.execute_run("ipmitool fru list")
            chassis_part_number = parser.get_value(r"Chassis Part Number[: ]+(\w+)\.\w+")

            self.execute_run("rmmod -f usb-storage")
            self.execute_run("rmmod -f ahci")
            self.execute_run("rmmod -f mpt3sas")
            self.execute_run("modprobe ahci")
            self.execute_run("modprobe mpt3sas")

            parser = self.execute_run(f"python {hwqc_pyc_path} -a {chassis_part_number} -m alibabacloud base",
                                      i_exit_code=True)

            result = parser.check_field(r"base[: ]+OK")
            if not result:
                # success_log_path = hwqc_factory_path
                self.copy_log("/tmp")
                self.fail("head HWQC fail")
            # else:
            #     fail_log_path = "/tmp"
            #     self.copy_log(success_log_path, fail_log_path)
            #     self.fail("head HWQC fail")

            parser = self.execute_run(f"ipmitool -I lanplus -H {tail_bmc_ip} -U admin -P admin fru list")
            chassis_part_number = parser.get_value(r"Chassis Part Number[: ]+(\w+)\.\w+")

            parser = self.execute_run(
                f"python {hwqc_pyc_path} -H {tail_bmc_ip} -U admin -P admin -a {chassis_part_number} -m alibabacloud all",
                i_exit_code=True)
            result = parser.check_field(r"base[: ]+OK")

            self.copy_log("/tmp")

            if not result:
                self.fail("tail HWQC fail")

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(HWQC)
