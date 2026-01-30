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
import re
import time

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

from Lib.Template import TempItem
from Utils.Constant import ErrorCode


class SpeedChange(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "SpeedChange"
        self.expect = "This is SpeedChange."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
        ]
    def setup(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            self.devices = self.get_bdf()
            self.logger.info("设备信息:{}".format(self.devices))
            self.dsp_bdf = self.devices["0000"][0]["eps"][0]["dsp"]
            self.ep_bdf = self.devices["0000"][0]["eps"][0]["ep"]
            self.speed_dict = {"2.5GT/s": 1, "5.0GT/s": 2, "8.0GT/s": 3, "16GT/s": 4, "32GT/s": 5}
    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            cap_speed_pre, cap_width_pre, self.current_speed_pre, current_width_pre = self.get_speed_width(self.ep_bdf)
            self.logger.info("速率变化前ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed_pre, self.current_speed_pre,
            ))
            self.speed_change(self.dsp_bdf, 1)
            cap_speed, cap_width, current_speed, current_width = self.get_speed_width(self.ep_bdf)
            self.logger.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            self.assertEqual("ffffffff", "速率变化验证", current_speed, "2.5GT/s")

            self.speed_change(self.dsp_bdf, 2)
            cap_speed, cap_width, current_speed, current_width = self.get_speed_width(self.ep_bdf)
            self.logger.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            self.assertEqual("ffffffff", "速率变化验证", current_speed, "5.0GT/s")

            self.speed_change(self.dsp_bdf, 3)
            cap_speed, cap_width, current_speed, current_width = self.get_speed_width(self.ep_bdf)
            self.logger.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            self.assertEqual("ffffffff", "速率变化验证", current_speed, "8.0GT/s")

            self.speed_change(self.dsp_bdf, 4)
            cap_speed, cap_width, current_speed, current_width = self.get_speed_width(self.ep_bdf)
            self.logger.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            self.assertEqual("ffffffff", "速率变化验证", current_speed, "16GT/s")

            self.speed_change(self.dsp_bdf, 5)
            cap_speed, cap_width, current_speed, current_width = self.get_speed_width(self.ep_bdf)
            self.logger.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            self.assertEqual("ffffffff", "速率变化验证", current_speed, "32GT/s")

    def tearDown(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            # 恢复测试前速率
            self.speed_change(self.dsp_bdf, self.speed_dict[self.current_speed_pre])
            cap_speed, cap_width, current_speed, current_width = self.get_speed_width(self.ep_bdf)
            self.logger.info("速率变化后ep_bdf:{} cap_speed:{} current_speed:{}".format(
                self.ep_bdf, cap_speed, current_speed
            ))
            self.assertEqual("ffffffff", "速率变化验证", current_speed, self.current_speed_pre)



