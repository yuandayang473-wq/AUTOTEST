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


class Mep_Flr(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Mep_Flr"
        self.expect = "This is Mep_Flr."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
        ]
    def setup(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            self.devices = self.get_bdf()
            self.logger.info("设备信息:{}".format(self.devices))
            self.mep_bdf = self.devices["0000"][0]["mep"]["ep"]
    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            self.flr(self.mep_bdf)
            self.sleep(5)
            self.assertEqual("FFFFFFFF", "FLR后验证driver信息", self.get_driver(self.mep_bdf), "nvme")




