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
            request.cls.speed_dict = {"2.5GT/s": 1, "5.0GT/s": 2, "8.0GT/s": 3, "16GT/s": 4, "32GT/s": 5}

            cap_speed_pre, cap_width_pre, request.cls.current_speed_pre, current_width_pre = METHOD.get_speed_width(request.cls.ep_bdf)
            LOGGER.info("速率变化前ep_bdf:{} cap_speed:{} current_speed:{}".format(
                request.cls.ep_bdf, cap_speed_pre, request.cls.current_speed_pre,
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
            assert current_speed == request.cls.current_speed_pre, "速率变化验证失败"

    @pytest.mark.author("袁大阳")
    def test_speed_change_001(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.speed_change(self.dsp_bdf, 1)
            cap_speed, cap_width, current_speed, current_width = METHOD.get_speed_width(self.ep_bdf)
            LOGGER.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            assert current_speed == "2.5GT/s", "速率变化验证失败"
    @pytest.mark.author("袁大阳")
    def test_speed_change_002(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.speed_change(self.dsp_bdf, 2)
            cap_speed, cap_width, current_speed, current_width = METHOD.get_speed_width(self.ep_bdf)
            LOGGER.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            assert current_speed == "5GT/s", "速率变化验证失败"


if __name__ == '__main__':
    pytest.main(['-s',"test_link_speed_change_new.py"])