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

import functools
from Lib.Config import YamlLoadConfig, JsonLoadConfig
from Lib.Login import SshConnect


class LoadConfig:

    def write_uut_yaml(self):
        device = YamlLoadConfig(cfg_path_name="Config", cfg_name="Device.yaml")
        UUT = {
            "UUT_01": {
                "ip_address": "127.0.0.1",
                "username": "root",
                "password": '123456'
            }
        }
        device.set_config(UUT)

    def load_config(self, logger):
        pass


class InitLoadConfig(LoadConfig):

    def __init__(self):
        pass

    def get_bmc_ip(self, logger):
        with SshConnect(ip="127.0.0.1", user="root", password="123456", logger=logger) as ssh:
            parser = ssh.run("ipmitool lan print").str_parser()
            bmc_ip = parser.get_value(r"IP Address[ :]+((?:[0-9]+\.){3}[0-9]+)")

        return bmc_ip

    def write_bmc_yaml(self, bmc_ip):
        bmc_device = YamlLoadConfig(cfg_path_name="Config", cfg_name="BmcDevice.yaml")
        bmc_data = {
            "BMC_01": {
                "ip_address": bmc_ip,
                "username": "sysadmin",
                "password": 'superuser'
            }
        }
        bmc_device.set_config(bmc_data)

    def load_config(self, logger):
        bmc_ip = self.get_bmc_ip(logger)
        self.write_uut_yaml()
        self.write_bmc_yaml(bmc_ip)


class PpuInitLoadConfig(InitLoadConfig):
    """
    python3 BatchRun.py --put put[根据指定execl选择要测试机器]
    """

    def __init__(self):
        super().__init__()

    def load_config(self, logger):
        head_bmc_ip, tail_bmc_ip = self.get_ppu_bmc_ip(logger)
        self.write_uut_yaml()
        self.write_ppu_bmc_yaml(head_bmc_ip, tail_bmc_ip)

    def get_ppu_bmc_ip(self, logger):
        with SshConnect(ip="127.0.0.1", user="root", password="123456", logger=logger) as ssh:
            parser = ssh.run("ipmitool lan print").str_parser()
            head_bmc_ip = parser.get_value(r"IP Address[ :]+((?:[0-9]+\.){3}[0-9]+)")

            parser = ssh.run("ipmitool -b 0x0a -t 0x32 lan print 1").str_parser()
            tail_bmc_ip = parser.get_value(r"IP Address[ :]+((?:[0-9]+\.){3}[0-9]+)")
        return head_bmc_ip, tail_bmc_ip

    def write_ppu_bmc_yaml(self, head_bmc_ip, tail_bmc_ip):
        bmc_device = YamlLoadConfig(cfg_path_name="Config", cfg_name="BmcDevice.yaml")

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
        bmc_device.set_config(bmc_data)


def load_mes_info(func):
    @functools.wraps(func)
    def wrapper(self):
        cfg = JsonLoadConfig(cfg_path_name="", cfg_name="mes_info.json").get_config()
        setattr(self, "mes_info", cfg)
        func(self)

    return wrapper


if __name__ == '__main__':
    PpuInitLoadConfig.load_config()
