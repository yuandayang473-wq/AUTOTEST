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
class TestSpeedChange:

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
            request.cls.speed_dict = {"2.5GT/s": 1, "5GT/s": 2, "8GT/s": 3, "16GT/s": 4, "32GT/s": 5}

            cap_speed_pre, cap_width_pre, request.cls.current_speed_pre, current_width_pre = METHOD.get_speed_width(request.cls.ep_bdf)
            LOGGER.info("速率变化前ep_bdf:{} cap_speed:{} current_speed:{}".format(
                request.cls.ep_bdf, cap_speed_pre, request.cls.current_speed_pre,
            ))
            METHOD.upload_file_to_server('Lib\\serial_check.py', 'serial_check.py', self.config.config["UUT"]["ip"],
                                         self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            request.cls.aer_info_before = METHOD.get_aer_status_info(request.cls.ep_bdf)
            if len(request.cls.devices["0000"]) >= 2:
                request.cls.dsp_bdf2 = request.cls.devices["0000"][1]["eps"][0]["dsp"]
                request.cls.ep_bdf2 = request.cls.devices["0000"][1]["eps"][0]["ep"]
                request.cls.aer_info_before2 = METHOD.get_aer_status_info(request.cls.ep_bdf2)
                cap_speed_pre2, cap_width_pre2, request.cls.current_speed_pre2, current_width_pre2 = METHOD.get_speed_width(request.cls.ep_bdf)
                LOGGER.info("速率变化前ep_bdf2:{} cap_speed2:{} current_speed2:{}".format(
                    request.cls.ep_bdf2, cap_speed_pre2, request.cls.current_speed_pre2,
                ))

        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.speed_change(request.cls.dsp_bdf, request.cls.speed_dict[request.cls.current_speed_pre])
            cap_speed, cap_width, current_speed, current_width = METHOD.get_speed_width(request.cls.ep_bdf)
            LOGGER.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                request.cls.ep_bdf, cap_speed, current_speed
            ))
            assert current_speed == request.cls.current_speed_pre, "恢复到测试之前的速率失败"
            if len(request.cls.devices["0000"]) >= 2:
                METHOD.speed_change(request.cls.dsp_bdf2, request.cls.speed_dict[request.cls.current_speed_pre2])
                cap_speed2, cap_width2, current_speed2, current_width2 = METHOD.get_speed_width(request.cls.ep_bdf2)
                LOGGER.info("速率变化后ep_bdf2:{} cap_speed2:{} current_speed2:{}".format(
                    request.cls.ep_bdf2, cap_speed2, current_speed2
                ))
                assert current_speed2 == request.cls.current_speed_pre2, "恢复到测试之前的速率失败"


    @pytest.mark.author("袁大阳")
    def test_pcie_sys_link_005(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.speed_change(self.dsp_bdf, 5)
            cap_speed, cap_width, current_speed, current_width = METHOD.get_speed_width(self.ep_bdf)
            LOGGER.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            assert current_speed == "32GT/s", "速率变化验证失败"
            if len(self.devices["0000"]) >= 2:
                METHOD.speed_change(self.dsp_bdf2, 5)
                cap_speed2, cap_width2, current_speed2, current_width2 = METHOD.get_speed_width(self.ep_bdf2)
                LOGGER.info("速率变化后ep_bdf2:{} cap_speed2:{} current_speed2:{}".format(
                    self.ep_bdf2, cap_speed2, current_speed2
                ))
                assert current_speed2 == "32GT/s", "速率变化验证失败"
            aer_info_after = METHOD.get_aer_status_info(self.ep_bdf)
            assert aer_info_after == self.aer_info_before, "retrain前后aer信息不同"
            if len(self.devices["0000"]) >= 2:
                aer_info_after2 = METHOD.get_aer_status_info(self.ep_bdf2)
                assert aer_info_after2 == self.aer_info_before2, "retrain前后aer信息不同"

    @pytest.mark.author("袁大阳")
    def test_pcie_sys_link_006(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.speed_change(self.dsp_bdf, 4)
            cap_speed, cap_width, current_speed, current_width = METHOD.get_speed_width(self.ep_bdf)
            LOGGER.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            assert current_speed == "16GT/s", "速率变化验证失败"
            if len(self.devices["0000"]) >= 2:
                METHOD.speed_change(self.dsp_bdf2, 4)
                cap_speed2, cap_width2, current_speed2, current_width2 = METHOD.get_speed_width(self.ep_bdf2)
                LOGGER.info("速率变化后ep_bdf2:{} cap_speed2:{} current_speed2:{}".format(
                    self.ep_bdf2, cap_speed2, current_speed2
                ))
                assert current_speed2 == "16GT/s", "速率变化验证失败"
            aer_info_after = METHOD.get_aer_status_info(self.ep_bdf)
            assert aer_info_after == self.aer_info_before, "retrain前后aer信息不同"
            if len(self.devices["0000"]) >= 2:
                aer_info_after2 = METHOD.get_aer_status_info(self.ep_bdf2)
                assert aer_info_after2 == self.aer_info_before2, "retrain前后aer信息不同"

    @pytest.mark.author("袁大阳")
    def test_pcie_sys_link_007(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.speed_change(self.dsp_bdf, 3)
            cap_speed, cap_width, current_speed, current_width = METHOD.get_speed_width(self.ep_bdf)
            LOGGER.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            assert current_speed == "8GT/s", "速率变化验证失败"
            if len(self.devices["0000"]) >= 2:
                METHOD.speed_change(self.dsp_bdf2, 3)
                cap_speed2, cap_width2, current_speed2, current_width2 = METHOD.get_speed_width(self.ep_bdf2)
                LOGGER.info("速率变化后ep_bdf2:{} cap_speed2:{} current_speed2:{}".format(
                    self.ep_bdf2, cap_speed2, current_speed2
                ))
                assert current_speed2 == "8GT/s", "速率变化验证失败"
            aer_info_after = METHOD.get_aer_status_info(self.ep_bdf)
            assert aer_info_after == self.aer_info_before, "retrain前后aer信息不同"
            if len(self.devices["0000"]) >= 2:
                aer_info_after2 = METHOD.get_aer_status_info(self.ep_bdf2)
                assert aer_info_after2 == self.aer_info_before2, "retrain前后aer信息不同"

    @pytest.mark.author("袁大阳")
    def test_pcie_sys_link_008(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.speed_change(self.dsp_bdf, 2)
            cap_speed, cap_width, current_speed, current_width = METHOD.get_speed_width(self.ep_bdf)
            LOGGER.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            assert current_speed == "5GT/s", "速率变化验证失败"
            if len(self.devices["0000"]) >= 2:
                METHOD.speed_change(self.dsp_bdf2, 2)
                cap_speed2, cap_width2, current_speed2, current_width2 = METHOD.get_speed_width(self.ep_bdf2)
                LOGGER.info("速率变化后ep_bdf2:{} cap_speed2:{} current_speed2:{}".format(
                    self.ep_bdf2, cap_speed2, current_speed2
                ))
                assert current_speed2 == "5GT/s", "速率变化验证失败"
            aer_info_after = METHOD.get_aer_status_info(self.ep_bdf)
            assert aer_info_after == self.aer_info_before, "retrain前后aer信息不同"
            if len(self.devices["0000"]) >= 2:
                aer_info_after2 = METHOD.get_aer_status_info(self.ep_bdf2)
                assert aer_info_after2 == self.aer_info_before2, "retrain前后aer信息不同"

    @pytest.mark.author("袁大阳")
    def test_pcie_sys_link_009(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.speed_change(self.dsp_bdf, 1)
            cap_speed, cap_width, current_speed, current_width = METHOD.get_speed_width(self.ep_bdf)
            LOGGER.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            assert current_speed == "2.5GT/s", "速率变化验证失败"
            if len(self.devices["0000"]) >= 2:
                METHOD.speed_change(self.dsp_bdf2, 1)
                cap_speed2, cap_width2, current_speed2, current_width2 = METHOD.get_speed_width(self.ep_bdf2)
                LOGGER.info("速率变化后ep_bdf2:{} cap_speed2:{} current_speed2:{}".format(
                    self.ep_bdf2, cap_speed2, current_speed2
                ))
                assert current_speed2 == "2.5GT/s", "速率变化验证失败"
            aer_info_after = METHOD.get_aer_status_info(self.ep_bdf)
            assert aer_info_after == self.aer_info_before, "retrain前后aer信息不同"
            if len(self.devices["0000"]) >= 2:
                aer_info_after2 = METHOD.get_aer_status_info(self.ep_bdf2)
                assert aer_info_after2 == self.aer_info_before2, "retrain前后aer信息不同"



if __name__ == '__main__':
    pytest.main(['-s',"test_link_speed_change_new.py"])