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
            request.cls.dsp_bdf1 = request.cls.devices["0000"][0]["eps"][0]["dsp"]
            request.cls.ep_bdf1 = request.cls.devices["0000"][0]["eps"][0]["ep"]
            METHOD.upload_file_to_server('Lib\\serial_check.py', 'serial_check.py', self.config.config["UUT"]["ip"],
                                         self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            request.cls.aer_info_before1 = METHOD.get_aer_status_info(request.cls.ep_bdf1)
            if len(request.cls.devices["0000"]) >= 2:
                request.cls.dsp_bdf2 = request.cls.devices["0000"][1]["eps"][0]["dsp"]
                request.cls.ep_bdf2 = request.cls.devices["0000"][1]["eps"][0]["ep"]
                request.cls.aer_info_before2 = METHOD.get_aer_status_info(request.cls.ep_bdf2)

        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.link_enable(self.dsp_bdf1, enable=True)
            if len(self.devices["0000"]) >= 2:
                METHOD.link_enable(self.dsp_bdf2, enable=True)

    @pytest.mark.author("袁大阳")
    def test_sys_link_002(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.link_enable(self.dsp_bdf1, enable=False)
            assert METHOD.read_config_lspci(self.ep_bdf1) == False, "链路disable后lspci -vvvs显示设备状态为正常"
            METHOD.link_enable(self.dsp_bdf1, enable=True)
            if len(self.devices["0000"]) >= 2:
                METHOD.link_enable(self.dsp_bdf2, enable=False)
                assert METHOD.read_config_lspci(self.ep_bdf2) == False, "链路disable后lspci -vvvs显示设备状态为正常"
                METHOD.link_enable(self.dsp_bdf2, enable=True)
            BASE.execute_run('python3 serial_check.py aer')
            aer_info_after1 = METHOD.get_aer_status_info(self.ep_bdf1)
            assert aer_info_after1 == self.aer_info_before1, "disable前后ep aer信息不同"
            if len(self.devices["0000"]) >= 2:
                aer_info_after2 = METHOD.get_aer_status_info(self.ep_bdf2)
                assert aer_info_after2 == self.aer_info_before2, "disable前后ep aer信息不同"

    @pytest.mark.author("袁大阳")
    def test_sys_link_003(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.link_enable(self.dsp_bdf1, enable=True)
            assert METHOD.read_config_lspci(self.ep_bdf1) == True, "链路enable后lspci -vvvs显示设备状态为异常"
            if len(self.devices["0000"]) >= 2:
                METHOD.link_enable(self.dsp_bdf2, enable=True)
                assert METHOD.read_config_lspci(self.ep_bdf2) == True, "链路enable后lspci -vvvs显示设备状态为异常"
            BASE.execute_run('python3 serial_check.py aer')
            aer_info_after1 = METHOD.get_aer_status_info(self.ep_bdf1)
            assert aer_info_after1 == self.aer_info_before1, "enable前后ep aer信息不同"
            if len(self.devices["0000"]) >= 2:
                aer_info_after2 = METHOD.get_aer_status_info(self.ep_bdf2)
                assert aer_info_after2 == self.aer_info_before2, "enable前后ep aer信息不同"


if __name__ == '__main__':
    pytest.main(['-s'])