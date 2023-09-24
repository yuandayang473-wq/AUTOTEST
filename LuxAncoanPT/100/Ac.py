# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncCpuCheck.py
@Time    :   2023/5/4
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/CPU测试 （机头）
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
from Lib.Login import ApcConnect
from Utils.Constant import ErrorCode


class Ac(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "ac"
        self.expect = "This is ac test script"

    def exe(self):
        data = self.platform.get_platform_data()

        if data and data.get("ip_address", None):
            jbmc_ip = data["ip_address"]

            pdu = self.platform.get_pdu_info()

            head_pdu_con = ApcConnect(ip=pdu["ip_address"], pdu_mode=pdu["pdu_model"], port=pdu["head_port"])
            tail_pdu_con = ApcConnect(ip=pdu["ip_address"], pdu_mode=pdu["pdu_model"], port=pdu["tail_port"])

            self.logger.info("server power off")
            head_pdu_con.pdu_off(self)
            if not self.platform.check_uut(action="off"):
                self.fail(ErrorCode.FFFFFFFF, "server power off fail")

            self.logger.info("jbog power off")
            tail_pdu_con.pdu_off(self)
            if not self.os_run.ping_ip(jbmc_ip):
                self.fail(ErrorCode.FFFFFFFF, "jbog power off fail")

            self.sleep(60)
            self.logger.info("jbog power on")
            tail_pdu_con.pdu_on(self)
            if not self.os_run.ping_ip(jbmc_ip, sleep_sec=15, action="on"):
                self.fail(ErrorCode.FFFFFFFF, "jbog power on fail")

            self.logger.info("server power on")
            head_pdu_con.pdu_on(self)
            if not self.platform.check_uut(action="on"):
                self.fail(ErrorCode.FFFFFFFF, "server power on fail")


if __name__ == '__main__':
    runner.single_runner(Ac)
