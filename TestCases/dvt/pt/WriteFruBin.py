# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Harvey
@Software:   TestCase
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
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
from Lib.Request import MesSocket
import subprocess
from collections import namedtuple

class WriteFruBin(TempItem):
    def os_cmd(self, command):
        """
        Execute OS system command
        :param command: system command can be executed in Linux Shell or Windows Command Prompt
        """
        self.logger.info(command)
        if not isinstance(command, str):
            raise TypeError(f'command MUST be _cmd string type, {command} is _cmd {type(command)} type')
        SysCMD = namedtuple('SysCMD', ['returncode', 'output'])
        p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,shell=True)
        stdout = p.stdout.decode(encoding='ascii')
        stderr = p.stderr.decode(encoding='ascii')
        output = stdout + stderr
        self.logger.info(output)
        return SysCMD(p.returncode, output)


    def __init__(self):
        super().__init__()
        self.name = "cpu config check"
        self.expect = "This is cpu config check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":self.locals["UUT"]},
            
            {"file": "BmcDevice.yaml", "name": "ADMIN", "key":self.locals["TAIL_TAOBAO_BMC"]},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key":self.locals["TAIL_ADMIN_BMC"]},
        ]
    def exe(self):
        with self.ssh_connect(uut=self.config["JBMC"]):
            data = self.execute_run("i2cset -y 5 0x70 2;i2ctransfer -y 5 w3@0x10 0x01 0x00 0x00")
            data = self.execute_run("i2cset -y 8 0x70 1;i2ctransfer -y 8 w3@0x10 0x02 0x20 0x00")
            data = self.execute_run("i2cset -y 8 0x70 2;i2ctransfer -y 8 w3@0x10 0x02 0x20 0x00 ")
            data = self.execute_run("gpiotool --set-dir-output 59;gpiotool --set-data-low 59;gpiotool --get-data 59")

        user = {
            "ip_address": "localhost",
            "password": "1",
            "username": "root"
        }
        
        with self.ssh_connect(uut=self.config["UUT"]):
            jbmc_ip = self.config["ADMIN"]["ip_address"]
            jbmc_user = self.config["ADMIN"]["username"]
            jbmc_passwd = self.config["ADMIN"]["password"]
            # path = os.path.split(os.path.realpath(__file__))[0]
            # path = path.split('/')[0:-1]
            # path.append("Utils")
            path = os.path.join(self.parent.globals["root_path"], "Utils")
            four_bin_path = path+"/ubb_40.bin"
            bp_bin_path = path+"/bp.bin"
            hib_bin_path = path+"/hib.bin"
            eighty_bin_path = path+"/fru_80fb.bin"
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 1 ", i_exit_code=True)
            parser = self.os_cmd(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru  write 1 {eighty_bin_path}  ").output
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 1 ", i_exit_code=True)
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 0 ", i_exit_code=True)
            parser = self.os_cmd(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru write 0 {hib_bin_path}  ").output
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 0 ", i_exit_code=True)
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 5 ", i_exit_code=True)
            parser = self.os_cmd(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru write 5 {four_bin_path}  ").output
            self.logger.info(parser)
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 5 ", i_exit_code=True)
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 2 ", i_exit_code=True)
            parser = self.os_cmd(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru write 2 {four_bin_path}  ").output
            self.logger.info(parser)
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 2 ", i_exit_code=True)
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 3 ", i_exit_code=True)
            parser = self.os_cmd(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru write 3 {bp_bin_path}  ").output
            self.logger.info(parser)
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 3 ", i_exit_code=True)
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 4 ", i_exit_code=True)
            parser = self.os_cmd(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru write 4 {bp_bin_path}  ").output
            self.logger.info(parser)
            data = self.execute_run(f"ipmitool  -I lanplus -H {jbmc_ip} -U {jbmc_user} -P {jbmc_passwd} fru print 4 ", i_exit_code=True)
            # self.assertEqual(f"clear bmc sel log", int(1), len(count))
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(WriteFruBin)

