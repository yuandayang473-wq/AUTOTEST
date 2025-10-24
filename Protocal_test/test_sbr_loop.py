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


class SbrLoop(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "SbrLoop"
        self.expect = "This is SbrLoop."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
        ]
    def setup(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            self.devices = self.get_switch_info()
        self.save_data_file(self.devices, '../pcie_tree_before.json')

    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            count = 2
            for i in range(count):
                self.logger.info("第{}次sbr test".format(count+1))
                for device in self.devices:
                    if device.type == 'DSP':
                        self.sbr_set(device.device_bdf)
                        self.read_config_lspci(device.device_bdf)
                        self.assertNotEqual(ErrorCode.FFFFFFFF, "dsp sbr test failed", self.ssh.get_exit_code(), 0)
                        self.devices = self.get_switch_info()
                        self.save_data_file(self.devices, 'pcie_tree_after.json')
                        self.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

                    # if device.type == 'USP':
                    #     self.sbr_set(device.device_bdf)
                    #     self.read_config_lspci(device.device_bdf)
                    #     self.assertNotEqual(ErrorCode.FFFFFFFF, "usp sbr test failed", self.ssh.get_exit_code(), 0)
                    #     self.devices = self.get_switch_info()
                    #     self.save_data_file(self.devices, 'pcie_tree_after.json')
                    #     self.execute_run('diff pcie_tree_before.json pcie_tree_after.json')
                    #
                    # if device.type == 'DMA':
                    #     self.sbr_set(device.parent)
                    #     self.read_config_lspci(device.parent)
                    #     self.assertNotEqual(ErrorCode.FFFFFFFF, "dma idsp sbr test failed", self.ssh.get_exit_code(), 0)
                    #     self.devices = self.get_switch_info()
                    #     self.save_data_file(self.devices, 'pcie_tree_after.json')
                    #     self.execute_run('diff pcie_tree_before.json pcie_tree_after.json')
                    #
                    # if device.type == 'MEP':
                    #     self.sbr_set(device.parent)
                    #     self.read_config_lspci(device.parent)
                    #     self.assertNotEqual(ErrorCode.FFFFFFFF, "mep idsp sbr test failed", self.ssh.get_exit_code(), 0)
                    #     self.devices = self.get_switch_info()
                    #     self.save_data_file(self.devices, 'pcie_tree_after.json')
                    #     self.execute_run('diff pcie_tree_before.json pcie_tree_after.json')





