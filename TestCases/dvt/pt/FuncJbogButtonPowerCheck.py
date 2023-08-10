# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncJbogButtonPowerCheck.py
@Time    :   2023/5/7
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/机头Button 测试/POWER Button
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
from Lib.Error import ErrItemFail


class FuncJbogButtonPowerCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "JBOG power button"
        self.expect = "This is JBOG power button function check test on the server"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "BmcDevice.yaml", "name": "SERVER_BMC", "key": self.locals["HEAD_BMC"]},
        ]

    def exe(self):
        # logger 获取 StreamHandler
        handler = self.logger.parent.handlers[0]

        with self.ssh_connect(uut=self.config["SERVER_BMC"]):
            parser = self.execute_run("ipmitool chassis power status")
            server_status = parser.get_value(r"Chassis Power is ([\w]+)")

        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            parser = self.execute_run("ipmitool chassis power status")
            jbog_status = parser.get_value(r"Chassis Power is ([\w]+)")

        # 初始化机头机尾开机
        if jbog_status.lower() == "off" and server_status.lower() == "off":
            #     先机尾开机，在机头开机
            for uut in [self.config["JBOG_BMC"], self.config["SERVER_BMC"]]:
                with self.ssh_connect(uut=uut):
                    parser = self.execute_run("ipmitool chassis power status")
                    server_off_status = parser.get_value(r"Chassis Power is ([\w]+)")
                    if server_off_status.lower() == "off":
                        self.execute_run("ipmitool chassis power on")

                    self.sleep(60)
                    for i in range(30):
                        parser = self.execute_run("ipmitool chassis power status")
                        server_off_status = parser.get_value(r"Chassis Power is ([\w]+)")
                        if server_off_status.lower() == "on":
                            break
                        self.sleep(15)
                    else:
                        return Fail(self, ErrItemFail("ipmitool chassis power on 开机失败"))

        # 先要确认机头关机了
        self.logger.info("SSH登录机头BMC")
        with self.ssh_connect(uut=self.config["SERVER_BMC"]):
            # 查看机头状态
            parser = self.execute_run("ipmitool chassis power status")
            server_off_status = parser.get_value(r"Chassis Power is ([\w]+)")
            # 开机状态，进行关机操作
            if server_off_status.lower() == "on":
                self.execute_run("ipmitool chassis power off")

            self.sleep(60)
            # 检查关机状态
            for i in range(30):
                parser = self.execute_run("ipmitool chassis power status")
                server_off_status = parser.get_value(r"Chassis Power is ([\w]+)")
                if server_off_status.lower() == "off":
                    break
                self.sleep(15)
            else:
                return Fail(self, ErrItemFail("机头关机失败"))

        self.sleep(2)
        self.logger.parent.removeHandler(self.logger.parent.handlers[0])
        tips = self.tips_msg("请长按 5s 机尾Power Button 关机 (G/g: Pass, R/r: Fail)")
        self.logger.info(tips)

        print(tips)
        select_tips = self.tips_msg("请输入选择字母[G/g R/r]: ")
        self.logger.info(select_tips)
        status = input(select_tips)
        self.logger.info(f"输入结果是: {status}")

        # logger日志器添加StreamHandler
        self.logger.parent.handlers.insert(0, handler)
        if status.lower() != 'g':
            return Fail(self, ErrItemFail("长按 5s 机尾Power Button 关机验证失败"))

        # 确认机尾已关机
        self.logger.info("SSH登录机尾BMC")
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            for i in range(30):
                parser = self.execute_run("ipmitool chassis power status")
                server_off_status = parser.get_value(r"Chassis Power is ([\w]+)")
                if server_off_status.lower() == "off":
                    self.logger.info("长按 5s 机尾Power Button 关机验证成功")
                    break
            else:
                return Fail(self, ErrItemFail("长按 5s 机尾Power Button 关机验证失败"))

        # 开机先机尾，后机头
        # 先机尾开机
        #   机尾开机
        self.sleep(60)
        self.logger.parent.removeHandler(self.logger.parent.handlers[0])
        tips = self.tips_msg("请短按机尾开机 (G/g: Pass, R/r: Fail)")
        self.logger.info(tips)
        print(tips)

        select_tips = self.tips_msg("请输入选择字母[G/g R/r]: ")
        self.logger.info(select_tips)

        status = input(select_tips)
        self.logger.info(f"输入结果是: {status}")
        # logger日志器添加StreamHandler
        self.logger.parent.handlers.insert(0, handler)

        if status.lower() != 'g':
            return Fail(self, ErrItemFail("短按机尾开机验证失败"))

        # 验证机尾短按是否成功
        self.logger.info("SSH登录机尾BMC")
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            for i in range(30):
                parser = self.execute_run("ipmitool chassis power status")
                server_off_status = parser.get_value(r"Chassis Power is ([\w]+)")
                if server_off_status.lower() == "on":
                    self.logger.info("短按机尾开机验证成功")
                    break
                self.sleep(15)
            else:
                return Fail(self, ErrItemFail("短按机尾开机验证失败"))

        # 机头开机
        self.logger.info("SSH登录机头BMC")
        with self.ssh_connect(uut=self.config["SERVER_BMC"]):
            parser = self.execute_run("ipmitool chassis power status")
            server_off_status = parser.get_value(r"Chassis Power is ([\w]+)")
            if server_off_status.lower() == "off":
                self.execute_run("ipmitool chassis power on")

            self.sleep(60)
            for i in range(30):
                parser = self.execute_run("ipmitool chassis power status")
                server_off_status = parser.get_value(r"Chassis Power is ([\w]+)")
                if server_off_status.lower() == "on":
                    break
                self.sleep(15)
            else:
                return Fail(self, ErrItemFail("机头开机失败"))

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(runner)
