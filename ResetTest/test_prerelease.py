# !/usr/bin/python3
# -*- encoding: utf-8 -*-
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



class TestCoolSoftReboot():

    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]
    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.sys(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))

    def test_cool_soft_reboot_001(self):
        ip = self.config.config["UUT"]["ip"]

        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            base_log_name = "{}_pretest0.log".format(time.strftime("%Y%m%d_%H%M%S"))
            BASE.execute_run(
                "python3 fw_check.py |tee {}".format(base_log_name))
        for i in range(1, 5):
            LOGGER.info("第{}次power cycle".format(i))
            with BASE.ssh_connect(uut=self.config.config["UUT"]):
                BASE.execute_run(
                    "ipmitool power cycle", i_exit_code=True)
            for j in range(20):
                SLEEP(25)
                BASE.os_run.run("ping -n 4 {}".format(ip), i_exit_code=True)
                if BASE.os_run.get_exit_code() == 0:
                    break
            else:
                raise Exception("500S仍未连接")
            with BASE.ssh_connect(uut=self.config.config["UUT"]):
                log_name = "{}_powercycle{}.log".format(time.strftime("%Y%m%d_%H%M%S"), i)
                BASE.execute_run(
                "python3 fw_check.py |tee {}".format(log_name))
                BASE.execute_run(
                "diff {} {}".format(log_name, base_log_name))

        for i in range(1, 5):
            LOGGER.info("第{}次reboot".format(i))
            with BASE.ssh_connect(uut=self.config.config["UUT"]):
                BASE.execute_run(
                    "reboot", i_exit_code=True)
            for j in range(20):
                SLEEP(25)
                BASE.os_run.run("ping -n 4 {}".format(ip), i_exit_code=True)
                if BASE.os_run.get_exit_code() == 0:
                    break
            else:
                raise Exception("500S仍未连接")

            with BASE.ssh_connect(uut=self.config.config["UUT"]):
                log_name = "{}_reboot{}.log".format(time.strftime("%Y%m%d_%H%M%S"), i)
                BASE.execute_run(
                "python3 fw_check.py |tee {}".format(log_name))
                BASE.execute_run(
                "diff {} {}".format(log_name, base_log_name))



