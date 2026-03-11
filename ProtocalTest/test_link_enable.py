# !/usr/bin/python3
# -*- encoding: utf-8 -*-
import sys
import subprocess

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
class TestLinkEnable:

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
            METHOD.upload_file_to_server('Lib\\serial_check.py', 'serial_check.py', self.config.config["UUT"]["ip"],
                                         self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            request.cls.aer_info_before = METHOD.get_aer_status_info(request.cls.ep_bdf)

        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.link_enable(self.dsp_bdf, enable=True)

    @pytest.mark.author("袁大阳")
    def test_sys_link_002(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.link_enable(self.dsp_bdf, enable=False)
            assert METHOD.read_config_lspci(self.ep_bdf) == False, "链路disable后lspci -vvvs显示设备状态为正常"
            BASE.execute_run('python3 serial_check.py aer')
            aer_info_after = METHOD.get_aer_status_info(self.ep_bdf)
            assert aer_info_after == self.aer_info_before, "disable前后ep aer信息不同"

    @pytest.mark.author("袁大阳")
    def test_sys_link_003(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.link_enable(self.dsp_bdf, enable=True)
            assert METHOD.read_config_lspci(self.ep_bdf) == True, "链路enable后lspci -vvvs显示设备状态为异常"
            BASE.execute_run('python3 serial_check.py aer')
            aer_info_after = METHOD.get_aer_status_info(self.ep_bdf)
            assert aer_info_after == self.aer_info_before, "enable前后ep aer信息不同"




if __name__ == '__main__':
    pytest.main(['-s'])