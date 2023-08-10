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
from TestCases.dvt.rt.PowerCycle import PowerCycle


class AcCycle(PowerCycle):

    def __init__(self):
        super().__init__()
        self.name = "PowerCycle-AC"
        
    def exe(self):
        self.os_ip = self.config["UUT"]["ip_address"]
        self.jbmc_ip = self.config["JBMC"]["ip_address"]
        
        for i in range(1,11):
            self.logger.info(f'================ power cycle ac : {i} cycle')
            #power cycle 
            self.power_cycle_ac()
            #清除机尾bmc log 

            with self.ssh_connect(uut=self.config["JBOG_BMC"]):
                parser = self.execute_run("ipmitool sel list")
                parser = self.execute_run("ipmitool alioem sel list")
                parser = self.execute_run("touch /logs/restorefactory")
                parser = self.execute_run("ipmitool sel clear")
                parser = self.execute_run("ipmitool raw 6 2", i_exit_code=True)
            with self.ssh_connect(uut=self.config["UUT"]):
                #清除机头bmc log 
                parser = self.execute_run("ipmitool sel list")
                parser = self.execute_run("ipmitool alioem sel list")
                self.execute_run(" ipmitool alioem restoretomanufacturesetting ", i_exit_code=True)
                self.sleep(120)
            with self.ssh_connect(uut=self.config["UUT"]):
                #初始化挂载
                self.inittool()
                #检查busid
                self.check_busid()
                #配置检查
                self.config_check()
                #健康检查
                self.health_check()
                #OAM 状态检查
                self.oam_chcek()
                #检查 时间
                self.check_times()
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(AcCycle)

