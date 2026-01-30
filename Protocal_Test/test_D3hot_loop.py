# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   yuandayang
@Contact :   Juncheng.Lu@ins-ict.com
@Software:   TestCase
@File    :   BmcFwcheck.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©ins  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import subprocess
import time

import pytest


from Lib import *


# load_list = ["LuxScript"]


# def load_package(path):
#     parent_folder = os.path.dirname(path)
#     for dirname in os.listdir(parent_folder):
#         if dirname in load_list:
#             sys.path.append(os.path.join(parent_folder, dirname))
#             load_list.pop(load_list.index(dirname))
#         if not load_list:
#             return None
#     else:
#         return load_package(parent_folder)
#
#
# load_package(os.path.abspath(__file__))
class TestD3hotLoop:

    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]
    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.sys(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            request.cls.devices = METHOD.get_bdf()
            LOGGER.info("设备信息:{}".format(request.cls.devices))
            request.cls.dsp_bdf = request.cls.devices["0000"][0]["eps"][0]["dsp"]
            request.cls.ep_bdf = request.cls.devices["0000"][0]["eps"][0]["ep"]
        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            LOGGER.info("恢复D0状态")
            METHOD.set_power_state(self.ep_bdf, "D0")

    def test_D3_hot_001(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.set_power_state(self.ep_bdf, "D3hot")
            SLEEP(4)
            reg_str = BASE.execute_run(f"lspci -vvvs {self.ep_bdf}").get_origin_data()
            METHOD.set_power_state(self.ep_bdf, "D0")
            SLEEP(2)

            LOGGER.info("开始执行D3hot循环测试")
            loop_count = 10
            for i in range(loop_count):
                LOGGER.info("第{}次循环".format(i+1))
                METHOD.set_power_state(self.ep_bdf, "D3hot")
                SLEEP(4)
                reg_str_each = BASE.execute_run(f"lspci -vvvs {self.ep_bdf}").get_origin_data()
                if reg_str_each != reg_str:
                    LOGGER.error("lspci -vvvs结果有变化，最初为\n{}，\n变为\n{}".format(reg_str, reg_str_each))
                METHOD.set_power_state(self.ep_bdf, "D0")
                SLEEP(2)

if __name__ == '__main__':
    pytest.main(['-s',"test_D3hot_loop.py"])