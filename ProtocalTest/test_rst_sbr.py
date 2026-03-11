# !/usr/bin/python3
# -*- encoding: utf-8 -*-
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
import pytest

from Lib import *
from Lib.Login import OsRunCmd


class TestRstSbr:
    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]

    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.sys(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            request.cls.devices = METHOD.get_switch_info()
            LOGGER.info("设备信息:{}".format(request.cls.devices))
            METHOD.save_data_file(request.cls.devices, 'pcie_tree_before.json')
            METHOD.upload_file_to_server('pcie_tree_before.json', 'pcie_tree_before.json',
                                     self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                     self.config.config["UUT"]["password"])
            METHOD.upload_file_to_server('Lib\\serial_check.py', 'serial_check.py', self.config.config["UUT"]["ip"],
                                     self.config.config["UUT"]["username"],
                                     self.config.config["UUT"]["password"])
        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))

    def test_pcie_sys_rst_003(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            LOGGER.info("开始执行sbr usp测试")
            for device in self.devices:
                if device.type == 'EP':
                    ep_bdf = device.device_bdf
            for device in self.devices:
                if device.type == 'USP':
                    METHOD.sbr_set(device.device_bdf)
                    assert METHOD.read_config_lspci(device.device_bdf) is True, "USP设备配置空间应该可读"
                    assert METHOD.read_config_lspci(ep_bdf) is False, "EP设备配置空间应该不可读"
                    self.devices_after = METHOD.get_switch_info()
                    METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
                    METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                                 self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                                 self.config.config["UUT"]["password"])
                    BASE.execute_run('python3 serial_check.py aer')
                    BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_pcie_sys_rst_004(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            LOGGER.info("开始执行sbr dsp测试")
            for device in self.devices:
                if device.type == 'DSP' and len(device.children) != 0:
                    METHOD.sbr_set(device.device_bdf)
                    assert METHOD.read_config_lspci(device.device_bdf) is True, "DSP设备配置空间应该可读"
                    self.devices_after = METHOD.get_switch_info()
                    METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
                    METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                                 self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                                 self.config.config["UUT"]["password"])
                    BASE.execute_run('python3 serial_check.py aer')
                    BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_pcie_sys_rst_005(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            LOGGER.info("开始执行sbr dma测试")
            for device in self.devices:
                if device.type == 'DMA_IDSP':
                    METHOD.sbr_set(device.device_bdf)
                    assert METHOD.read_config_lspci(device.device_bdf) is True, "DMA_IDSP设备配置空间应该可读"
                    self.devices_after = METHOD.get_switch_info()
                    METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
                    METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                                 self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                                 self.config.config["UUT"]["password"])
                    BASE.execute_run('python3 serial_check.py aer')
                    BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_pcie_sys_rst_006(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            LOGGER.info("开始执行sbr mep测试")
            for device in self.devices:
                if device.type == 'MEP_IDSP':
                    METHOD.sbr_set(device.device_bdf)
                    assert METHOD.read_config_lspci(device.device_bdf) is True, "MEP_IDSP设备配置空间应该可读"
                    self.devices_after = METHOD.get_switch_info()
                    METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
                    METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                                 self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                                 self.config.config["UUT"]["password"])
                    BASE.execute_run('python3 serial_check.py aer')
                    BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')
