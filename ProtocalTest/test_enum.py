# !/usr/bin/python3
# -*- encoding: utf-8 -*-
import base64
import os

import pytest
import time


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
class TestEnum:

    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]
    bdf = None
    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.info(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            request.cls.devices = METHOD.get_switch_info()
            LOGGER.info("设备信息:{}".format(request.cls.devices))
            METHOD.save_data_file(request.cls.devices, 'pcie_tree_before.json')
            METHOD.upload_file_to_server('pcie_tree_before.json', 'pcie_tree_before.json',
                                         self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
        yield
        # teardown
        LOGGER.info(f"结束执行测试用例组:{request.cls}".center(100, "-"))

    @pytest.mark.env_hint("需要环境中有nvme设备")
    def test_pcie_sys_enum_002(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for device in self.devices:
                if device.class_code == "0108" and device.type == "EP":
                    self.bdf = device.device_bdf
                    self.driver = device.driver
            assert self.bdf is not None, "未找到class code为0108的设备，请确认测试环境中是有NVME设备"
            # 卸载ep driver并重新加载
            BASE.execute_run(f"echo {self.bdf} > /sys/bus/pci/drivers/{self.driver}/unbind")
            BASE.execute_run(f"echo {self.bdf} > /sys/bus/pci/drivers/{self.driver}/bind")
            # 再次获取一次driver，确认驱动重新绑定成功
            assert METHOD.get_driver(self.bdf) == self.driver
            # 加载dma driver后卸载
            BASE.execute_run("lsmod|grep yundu_dma", i_exit_code=True)
            if BASE.ssh.get_exit_code() != 0:
                METHOD.insmod_dma_driver(self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
                METHOD.rmmod_dma_driver()
            else:
                METHOD.rmmod_dma_driver()
                METHOD.insmod_dma_driver(self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])


if __name__ == '__main__':
    pytest.main([ "ProtocalTest/test_enum.py"] )