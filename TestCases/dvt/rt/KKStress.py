# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   KKStress.py
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

from Lib.Result import Pass
from Lib.Template import TempItem
from Lib.Runner import runner


class KKStress(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "kk stress"
        self.expect = "This is kk stress test"


        # UUT = {
        #     "ip_address": "192.2.37.184",
        #     "username": "root",
        #     "password": '123456'
        # }

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key": self.locals["TAIL_TAOBAO_BMC"]},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            # {"file": "Device.yaml", "name": "UUT", "key": UUT},
            {"file": "UUT.yaml", "name": "path", "key": "InitPath"},
        ]

    def init_env(self):
        path = self.config["path"]

        mount_path = path.get('mount_path')
        test_path = path.get('test_path')
        alidriver_source_rpm = os.path.join(f"{mount_path}", f"{path.get('aliaom_driver')}")
        kingkong_tools = os.path.join(f"{path['mount_path']}", "kingkong")
        kingkong_source_zip = os.path.join(f"{kingkong_tools}", f"{path['kingkong']}")
        kingkong_target_zip = os.path.join(path["test_path"], path["kingkong"])
        kk_path = os.path.join("/root", path["kingkong"][:-4])
        kk_tools = os.path.join(kk_path, "tools")
        Ppu_source_zip = os.path.join(kingkong_tools, path["kingkong_Ppu_zip"])
        Ppu_target_zip = os.path.join(kk_tools, path["kingkong_Ppu_zip"])
        Ppu_path = os.path.join(kk_tools, path["kingkong_Ppu_zip"][:-4])
        btv_source_file = os.path.join(kingkong_tools, path["kingkong_btv"])

        # mount
        self.execute_run(f'''df | grep -iE "{path['source_path']}.*/mnt"''', save_exit_code=True, desc="is mount /mnt")
        if self.ssh.get_exit_code() != 0:
            self.execute_run(f"{path['mount_cmd']}")

        self.execute_run(f"[ ! -d {test_path} ] && mkdir -p {test_path}", i_exit_code=True)
        # cp file
        self.execute_run(f"\cp {alidriver_source_rpm} {test_path}")
        self.execute_run(f"\cp {kingkong_source_zip} {test_path}")

        # unzip kingkong zip
        self.execute_run(f"rm -rf {kk_path}")
        self.execute_run(f"unzip {kingkong_target_zip}")

        # cp Ppu.zip to tools
        self.execute_run(f"cp {Ppu_source_zip} {kk_tools}")

        # 删除old Ppu
        self.execute_run(f"rm -rf {Ppu_path}")
        self.execute_run(f"unzip -d {kk_tools} {Ppu_target_zip}")

        self.execute_run(f"cp {btv_source_file} {Ppu_path}")

        # rpm 安装driver
        self.execute_run(f"rpm -ivh --nodeps --force {path.get('test_path')}{path.get('aliaom_driver')}")

        # chmod_cmd = f"chmod 777 -R {kk_path}"
        self.kk_path = kk_path

    def copy_kk_log(self):
        path = self.config["path"]
        rk = self.parent.globals["RK"]
        # rk = "RK0037030024"
        put = self.locals["PUT"]
        # put = "PUT110"
        sn = self.parent.globals["SN"]

        log_path = os.path.join(path.get("mount_path"), 'kklog', f"{put}_{rk}_{sn}")
        self.execute_run(f"[ ! -d {log_path} ] && mkdir -p {log_path}", i_exit_code=True)

        # 拷贝kk log
        kk_log_path = os.path.join(self.kk_path, "kklog*.tar.xz")
        self.execute_run(f"cp {kk_log_path} {log_path}")

    def enable_ifs(self):
        """
        <Enable IFS>
        ipmitool raw 0x3e 0x5c 0x00 0x01 0x81
        ipmitool raw 0x3e 0x5c 0x37 0x01 0x81

        <Disable IFS (关闭主开关和所有依赖开关)>
        ipmitool raw 0x3e 0x5c 0x00 0x01 0x81
        ipmitool raw 0x3e 0x5c 0x37 0x01 0x80

        <Read IFS Status>
        ipmitool raw 0x3e 0x5f 0x37 0x01
        返回的01 80中, 第二个字节代表状态, 80即0x80即Disabled, 81即0x81即Enable,
        :return:
        """
        for i in range(3):
            with self.ssh_connect(uut=self.config['UUT']):

                parser = self.execute_run("ipmitool raw 0x3e 0x5f 0x37 0x01", parser_type="raw_parser")
                status = parser.raw_str(1)
                if status == "81":
                    break

                self.execute_run("ipmitool raw 0x3e 0x5c 0x00 0x01 0x81")
                self.execute_run("ipmitool raw 0x3e 0x5c 0x37 0x01 0x81")
                self.execute_run("reboot", i_exit_code=True)

            self.sleep(150)

            with self.ssh_connect(uut=self.config["UUT"]):
                parser = self.execute_run("ipmitool raw 0x3e 0x5f 0x37 0x01", parser_type="raw_parser")
                status = parser.raw_str(1)
                if status == "81":
                    break
        else:
            self.fail("enable IFS")

    def clear_sel_log(self):
        # 清除机尾alioem sel
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            self.execute_run("touch /logs/restorefactory")
            self.execute_run("ipmitool raw 6 2")

        self.sleep(120)

        # 清除机头alioem sel
        # with self.ssh_connect(uut=self.config["SERVER_BMC"]):
        #     parser = self.execute_run("touch /logs/restorefactory")
        #     parser = self.execute_run("ipmitool raw 6 2")
        # self.sleep(30)

        jbmc_ip = self.config["JBMC"]["ip_address"]
        jbmc_user = self.config["JBMC"]["username"]
        jbmc_passwd = self.config["JBMC"]["password"]
        with self.ssh_connect(uut=self.config["UUT"]):
            self.execute_run(f"ipmitool -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} sel clear ")
            self.execute_run(f"ipmitool -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} sel list")
            # self.assertEqual(f"clear Jbog bmc sel log", int(1), len(count))

            # 清除机头alioem sel 机头 sel log
            self.execute_run("ipmitool alioem restoretomanufacturesetting")
            self.sleep(120)
            parser = self.execute_run("ipmitool sel list")
            # records = parser.split(r"\n")
            # self.assertLessEqual(f"clear Server bmc sel log", len(records), 2)

    def tearDown(self):
        for i in range(3):
            with self.ssh_connect(uut=self.config['UUT']):
                parser = self.execute_run("ipmitool raw 0x3e 0x5f 0x37 0x01", parser_type="raw_parser")
                status = parser.raw_str(1)
                if status == "80":
                    break
                self.execute_run("ipmitool raw 0x3e 0x5c 0x00 0x01 0x81")
                self.execute_run("ipmitool raw 0x3e 0x5c 0x37 0x01 0x80")
                self.execute_run("reboot", i_exit_code=True)

            self.sleep(150)

            with self.ssh_connect(uut=self.config["UUT"]):
                parser = self.execute_run("ipmitool raw 0x3e 0x5f 0x37 0x01", parser_type="raw_parser")
                status = parser.raw_str(1)
                if status == "80":
                    break
        else:
            self.fail("disable IFS")

    def exe(self):

        self.enable_ifs()
        self.clear_sel_log()

        with self.ssh_connect(uut=self.config["UUT"]):
            self.init_env()

            # path = self.config["path"]
            # self.kk_path = os.path.join("/root", path["kingkong"][:-4])

            cmd = f"python {self.kk_path}/kk.pyc -t default -m default -c {self.kk_path}/testcase/testcase_full.yaml > kkout 2>&1"
            cmd_timeout = 60 * 60 * 26
            self.execute_run(cmd, cmd_timeout=cmd_timeout, i_timeout_err=True, i_exit_code=True)

            # kklog = os.path.join(self.kk_path, "kklog")
            TestReport = os.path.join(self.kk_path, "kklog", "TestReport.yaml")

            # self.execute_run(f"cp /root/TestReport.yaml {kklog}")

            self.execute_run(f"cat {TestReport}", retry_expt=1)
            cat_kk_cmd = f"cat {TestReport} |grep -i 'Result: FAIL'"
            self.execute_run(cat_kk_cmd, save_exit_code=True)
            if self.ssh.get_exit_code() == 0:  # TestReport.yaml 有 Result: FAIL
                self.fail("TestReport.yaml found 'Ressult: FAIL'")

            self.copy_kk_log()

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(KKStress)

