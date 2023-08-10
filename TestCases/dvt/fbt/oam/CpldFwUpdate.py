# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   CpldFwUpdate.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
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

from Lib.Result import Pass
from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Login import ApcConnect


class CpldFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpld fw update"
        self.expect = "This is cpld fw update for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "BmcDevice.yaml", "name": "BMC_HEADER", "key": self.locals["HEAD_BMC"]},
            {"file": "PduDevice.yaml", "name": "pdu", "key": self.locals["PDU"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]
        self.flash_flag = False

    def exe(self):
        tail_bmc_ip = self.config["BMC_TAIL"]["ip_address"]
        FwVsersion = self.config["FwVsersion"]
        path = self.config["InitPath"]
        self.ubb1_flag = False
        self.ubb2_flag = False
        user = {
            "ip_address": "localhost",
            "password": "1",
            "username": "root"
        }

        current_versions = {
            'ubb1': '',
            'ubb2': '',
        }

        with self.ssh_connect(uut=self.config["BMC_TAIL"]):
            parser = self.execute_run("i2ctransfer -y 13 w2@0x20 0x00 0x05 r1", desc="ubb1 cpld version")
            current_versions['ubb1'] = parser.get_origin_data().strip()
            parser = self.execute_run("i2ctransfer -y 13 w2@0x34 0x00 0x05 r1", desc="ubb2 cpld version")
            current_versions['ubb2'] = parser.get_origin_data().strip()

        with self.ssh_connect(uut=user):

            self.execute_run(f"ipmitool -I lanplus -H {tail_bmc_ip} -U admin -P admin power off")
            self.sleep(20)
            # ubb1
            self.logger.info("========================Start UBB1 fw update Test===========================")
            self.logger.info(
                f"Current ubb1 cpld version is: {current_versions['ubb1']}, target version is {FwVsersion.get('ubb1')}")
            if current_versions['ubb1'] != FwVsersion.get("ubb1"):
                flag = "update"
                self.flash_flag = True
                self.execute_run("chmod -R 777 /opt/Alioam/")
                parser = self.execute_run(
                    f"{path['ubb1_cpld_script']} {tail_bmc_ip} admin admin {path['ubb1_cpld_fw']}")
                if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                    self.logger.info("Tail ubb1 flash bure fail")
                    self.fail("Tail ubb1 flash bure fail")
                self.ubb1_flag = True
            else:
                flag = "un update"
            self.logger.info(f"current version: {current_versions['ubb1']} target version: {FwVsersion.get('ubb1')} update status: {flag}")
            self.logger.info("========================End UBB1 fw update Test=============================")

            # UBB2 
            self.logger.info("======================Start UBB2 fw update Test==========================")
            self.logger.info(
                f"Current ubb2 cpld version is: {current_versions['ubb2']}, target version is {FwVsersion.get('ubb2')}")
            if current_versions['ubb2'] != FwVsersion.get("ubb2"):
                flag = "update"
                self.flash_flag = True
                self.execute_run("chmod -R 777 /opt/Alioam/")
                parser = self.execute_run(
                    f"{path['ubb2_cpld_script']} {tail_bmc_ip} admin admin {path['ubb2_cpld_fw']}")
                if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                    self.logger.info("Tail ubb2 flash bure fail")
                    self.fail("Tail ubb2 flash bure fail")
                self.ubb2_flag = True
            else:
                flag = "un update"
            self.logger.info(f"current version: {current_versions['ubb2']} target version: {FwVsersion.get('ubb2')} update status: {flag}")
            self.logger.info("========================End UBB2 fw update Test=============================")

        return Pass(self)

    def tearDown(self):
        if self.ubb1_flag and self.ubb2_flag:
            tail_bmc_ip = self.config["BMC_TAIL"]["ip_address"]
            header_bmc_ip = self.config["BMC_HEADER"]["ip_address"]
            path = self.config["InitPath"]
            # ac 操作
            user = {
                "ip_address": "localhost",
                "password": "1",
                "username": "root"
            }
            pdu = self.config["pdu"]
            head_pdu_con = ApcConnect(ip=pdu["ip_address"], pdu_mode=pdu["pdu_model"], port=pdu["head_port"])
            tail_pdu_con = ApcConnect(ip=pdu["ip_address"], pdu_mode=pdu["pdu_model"], port=pdu["tail_port"])
            with self.ssh_connect(uut=user):
                # 机头下电
                flag1 = False
                for i in range(1, 11):
                    self.logger.info(f"Server power off run time: {i}")
                    head_pdu_con.pdu_off(self)
                    parser = self.execute_run(f"ping {header_bmc_ip} -c4", i_exit_code=True)
                    if re.search(r'100\%\s*packet\s*loss', parser.get_origin_data(), re.I):
                        flag1 = True
                    if flag1:
                        break
                    self.sleep(10)
                if not flag1:
                    self.fail("Server power off statu: fail")
                # 机尾下点后delay 30s
                self.sleep(30)

                # 机尾下电
                flag2 = False
                for i in range(1, 11):
                    self.logger.info(f"Jbog power off run time: {i}")
                    tail_pdu_con.pdu_off(self)
                    parser = self.execute_run(f"ping {tail_bmc_ip} -c4", i_exit_code=True)
                    if re.search(r'100\%\s*packet\s*loss', parser.get_origin_data(), re.I):
                        flag2 = True
                    if flag2:
                        break
                    self.sleep(10)
                if not flag2:
                    self.fail("Jbog power off statu: fail")

                # 机头机尾下电后delay 60s
                self.sleep(60)

                # 机尾上电
                flag3 = False
                for i in range(1, 11):
                    self.logger.info(f"Jbog power on run time: {i}")
                    tail_pdu_con.pdu_on(self)
                    parser = self.execute_run(f"ping {tail_bmc_ip} -c4", i_exit_code=True)
                    if re.search(r' 0\%\s*packet\s*loss', parser.get_origin_data(), re.I):
                        flag3 = True
                    if flag3:
                        break
                    self.sleep(10)
                if not flag3:
                    self.fail("Jbog power on statu: fail")

                # 机头上电后delay 300s 等待机尾完全启动
                self.sleep(300)

                # 机头上电
                flag4 = False
                for i in range(1, 11):
                    self.logger.info(f"Server power on run time: {i}")
                    head_pdu_con.pdu_on(self)
                    parser = self.execute_run(f"ping {tail_bmc_ip} -c4", i_exit_code=True)
                    if re.search(r' 0\%\s*packet\s*loss', parser.get_origin_data(), re.I):
                        flag4 = True
                    if flag4:
                        break
                    self.sleep(10)
                if not flag4:
                    self.fail("Server power on statu: fail")

            self.sleep(300)
            # 等待ac, 等待机尾 bmc 起来
            with self.ssh_connect(uut=self.config["BMC_TAIL"], login_retry=10):
                pass
            # 等待机头 os 起来
            with self.ssh_connect(uut=self.config["UUT"], login_retry=10):
                parser = self.execute_run("reboot", i_exit_code=True)
            self.sleep(150)

            with self.ssh_connect(uut=self.config["UUT"], login_retry=10):
                self.execute_run("ip a")

            with self.ssh_connect(uut=self.config["UUT"]):
                # self.execute_run(f'''[[ `df | grep -iE "//192.2.19.51/share.*/mnt"` != '' ]] || mount -t cifs -o vers=2.0,username=Administrator,password=\`1q,sec=ntlmssp,cache=none,nobrl {path.get('source_path')} /mnt''',i_exit_code=True)
                # self.execute_run(f"rpm -ivh {path.get('mount_path')}sshpass-1.09-4.el8.x86_64.rpm ",i_exit_code=True)
                # self.execute_run(f"[ ! -d {path.get('fru_path')} ] && mkdir -p {path.get('fru_path')} ")
                # self.execute_run(f"rm -rf {path.get('fru_path')}/* ")
                # self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('aliaom_driver')} {path.get('test_path')} ")
                # self.execute_run(f"rpm -ivh --nodeps --force {path.get('test_path')}{path.get('aliaom_driver')} ")
                # self.execute_run(f"cp -rf /mnt/fru/* {path.get('fru_path')}")
                # self.execute_run(f"[ ! -d {path.get('fw_path')} ] && mkdir -p {path.get('fw_path')}",i_exit_code=True)
                # self.execute_run(f"rm -rf {path.get('fw_path')}/* ")
                # self.execute_run(f"\cp -rf {path['fw_source_path']} {path.get('fw_path')}")
                # self.execute_run(f"cp -rf {path['mount_path']}kingkong/{path['kingkong']} {path.get('test_path')} ")
                # self.execute_run("chmod -R 777 /opt/Alioam/")
                # self.execute_run(f'{path["oampower_read_script"]}')

                self.execute_run(f'''df | grep -iE "{path['source_path']}.*/mnt"''', save_exit_code=True)
                if self.ssh.get_exit_code() != 0:
                    # self.execute_run("mount -t cifs -o vers=2.0,username=Administrator,password=\`1q,sec=ntlmssp,cache=none,nobrl {path.get('source_path')} /mnt")
                    self.execute_run(f"{path['mount_cmd']}")

                self.execute_run(f"ls {path.get('fw_path')}", save_exit_code=True)
                if self.ssh.get_exit_code() != 0:
                    #  创建文件加
                    self.execute_run(f"mkdir -p {path.get('fw_path')}")

                self.execute_run(f"ls {path.get('fru_path')}", save_exit_code=True)
                if self.ssh.get_exit_code() != 0:
                    #  创建文件加
                    self.execute_run(f"mkdir -p {path.get('fru_path')}")

                # self.execute_run(f"rm -rf {path.get('fw_path')}*")
                # self.execute_run(f"rm -rf {path.get('fru_path')}*")

                self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('aliaom_driver')} {path.get('test_path')}")
                self.execute_run(f"cp -rf {path['fw_source_path']} {path.get('fw_path')}")
                self.execute_run(f"cp -rf {path['mount_path']}kingkong/{path['kingkong']} {path.get('test_path')}")
                self.execute_run(f"cp -rf /mnt/fru/* {path.get('fru_path')}")

                self.execute_run(f"rpm -ivh --nodeps --force {path.get('test_path')}{path.get('aliaom_driver')}")
                self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}mft-4.20.1-14.x86_64.rpm")
                self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}sshpass-1.09-4.el8.x86_64.rpm")

                self.execute_run("chmod -R 777 /opt/Alioam/")

                # self.execute_run(f'{path["oampower_read_script"]}')


if __name__ == '__main__':
    runner.single_runner(CpldFwUpdate)

