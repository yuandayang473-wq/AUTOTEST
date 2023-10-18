# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   KKStress_2.py
@Time    :   2023/5/9
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   健康检查
'''
import os
import sys
import time

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


class KKStress_2(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "kk stress"
        self.expect = "This is kk stress test"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key": "BMC_02"},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": "BMC_01"},
            {"folder": "Luxshare-AnconaRT1/100/Config", "file": "UUT.yaml", "name": "kingkong_path",
             "key": "tools/ancoan/kingkong"},
            {"folder": "Luxshare-AnconaRT1/100/Config", "file": "UUT.yaml", "name": "kingkong_info",
             "key": "tools.ancoan.kingkong"},
            {"folder": "Luxshare-AnconaRT1/100/Config", "file": "UUT.yaml", "name": "rpm", "key": "tools/ancoan/rpm"},
            {"folder": "Luxshare-AnconaRT1/100/Config", "file": "UUT.yaml", "name": "rpm_info",
             "key": "tools.ancoan.rpm"},
        ]

    @load_mes_info
    def init_env(self):
        http_server_url = self.mes_info["info"]["http_server_url"]
        _kingkong = os.path.join(http_server_url, f"LuxScript/tools/ancoan/kingkong/")
        ali_driver = os.path.join(http_server_url,
                                  f"LuxScript/tools/ancoan/rpm/{self.config['rpm_info']['aliaom_driver']}")

        self.wget(_kingkong)
        self.wget(ali_driver)

        kingkong_zip_path = self.config["kingkong_path"]["kingkong"]
        kingking_dir_name = self.config["kingkong_info"]["kingkong_name"]
        btv_tar_path = self.config["kingkong_path"]["btv_tar"]
        ppu_dir_name = self.config["kingkong_info"]["kingkong_Ppu_name"]
        kk_tools = os.path.join("/root", kingking_dir_name, "tools")
        rpm = self.config["rpm"]

        Ppu_zip_path = self.config["kingkong_path"]["kingkong_Ppu_zip"]
        Ppu_path = os.path.join("/root", kingking_dir_name, "tools", ppu_dir_name)

        self.os_run.run(f"rm -rf /root/{kingking_dir_name}")
        self.os_run.run(f"unzip -d /root {kingkong_zip_path}")

        # 删除old Ppu
        self.os_run.run(f"rm -rf {Ppu_path}")
        self.os_run.run(f"unzip -d {kk_tools} {Ppu_zip_path}")

        self.os_run.run(f"cp {btv_tar_path} {Ppu_path}")

        # rpm 安装driver
        self.os_run.run(f"rpm -ivh --nodeps --force {rpm['aliaom_driver']}")

        # chmod_cmd = f"chmod 777 -R {kk_path}"

    def copy_kk_log(self):
        # 拷贝kk log
        kk_log_path = os.path.join("/root", self.config["kingkong_info"]["kingkong_name"], "kklog*.tar.xz")
        sn = self.mes_info['info']["sn"]
        from_format = "%Y_%m_%d_%H_%M_%S"
        to_format_2 = "%Y%m%d%H%M%S"
        struct_time = time.strftime(from_format, time.localtime())
        time_struct = time.strptime(struct_time, from_format)
        settime = time.strftime(to_format_2, time_struct)

        self.os_run.run(f"cp {kk_log_path} {self.CUSTOM_LOG_PATH}")
        self.os_run.run(f"mkdir {self.CUSTOM_LOG_PATH}/Luxshare-PPU_Kingkong_Test")
        self.os_run.run(f"cd {self.CUSTOM_LOG_PATH}; zip -r -q {self.CUSTOM_LOG_PATH}/Luxshare-PPU_Kingkong_Test/{sn}{settime}.zip *.tar.xz")
        self.os_run.run(f"rm -rf {self.CUSTOM_LOG_PATH}/kklog*.tar.xz")

    def check_enable_ifs(self):
        parser = self.os_run.run("ipmitool raw 0x3e 0x5f 0x37 0x01", parser_type="raw_parser")
        status = parser.raw_str(1)
        if status != "81":
            self.fail(ErrorCode.FFFFFFFF, "enable IFS")

    def clear_sel_log(self):
        # 清除机尾alioem sel
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            self.execute_run("touch /logs/restorefactory")
            self.execute_run("ipmitool raw 6 2")

        self.sleep(120)

        jbmc_ip = self.config["JBMC"]["ip_address"]
        jbmc_user = self.config["JBMC"]["username"]
        jbmc_passwd = self.config["JBMC"]["password"]

        self.os_run.run(f"ipmitool -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} sel clear ")
        self.os_run.run(f"ipmitool -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} sel list")
        # self.assertEqual(f"clear Jbog bmc sel log", int(1), len(count))

        # 清除机头alioem sel 机头 sel log
        self.os_run.run("ipmitool alioem restoretomanufacturesetting")
        self.sleep(120)
        self.os_run.run("ipmitool sel list")

    def tearDown(self):
        parser = self.os_run.run("ipmitool raw 0x3e 0x5f 0x37 0x01", parser_type="raw_parser")
        status = parser.raw_str(1)
        if status == "80":
            self.platform.run(cmd="")
            self.platform.skip_dynamic_tool("not need reboot")
            return

        self.os_run.run("ipmitool raw 0x3e 0x5c 0x00 0x01 0x81")
        self.os_run.run("ipmitool raw 0x3e 0x5c 0x37 0x01 0x80")
        self.platform.run(cmd="reboot")

    def exe(self):

        self.check_enable_ifs()
        self.clear_sel_log()

        self.init_env()

        kk_path = os.path.join("/root",self.config["kingkong_info"]["kingkong_name"])
        cmd = f"python {kk_path}/kk.pyc -t default -m default -c {kk_path}/testcase/testcase_full.yaml > kkout 2>&1"
        cmd_timeout = 60 * 60 * 26
        with self.ssh_connect(uut=self.config["UUT"]):
            self.execute_run(cmd, cmd_timeout=cmd_timeout, i_timeout_err=True, i_exit_code=True)

        TestReport = os.path.join(kk_path, "kklog", "TestReport.yaml")

        self.os_run.run(f"cat {TestReport}", retry_expt=1)
        cat_kk_cmd = f"cat {TestReport} |grep -i 'Result: FAIL'"
        self.os_run.run(cat_kk_cmd, i_exit_code=True, save_exit_code=True)
        if self.os_run.get_exit_code() == 0:  # TestReport.yaml 有 Result: FAIL
            self.fail(ErrorCode.FFFFFFFF, "TestReport.yaml found 'Ressult: FAIL'")

        self.copy_kk_log()


if __name__ == '__main__':
    runner.single_runner(KKStress_2)
