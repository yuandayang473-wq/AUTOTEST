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
class TestPerformanceCx7Ib:

    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]
    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.sys(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            # all_devices = METHOD.get_switch_info()
            # cx7_list = METHOD.get_special_device(all_devices, "EP_NETWORK_CX7")
            # cx7_bdf_list = [device.device_bdf for device in cx7_list]
            # request.cls.numa_node = METHOD.get_device_numa_node(cx7_bdf_list[0])
            request.cls.numa_node = "0"
            devices = METHOD.get_cx7_devices()
            request.cls.rdma_devices = devices["rdmalink"]
            request.cls.ip_devices = devices["ip"]
            LOGGER.info("RDMA设备信息:{}".format(request.cls.rdma_devices))
            LOGGER.info("IP设备信息:{}".format(request.cls.ip_devices))
            METHOD.start_opensm()
            METHOD.net_test_set_up(request.cls.ip_devices)
        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.kill_ib_process()
            METHOD.clear_netns()

    @pytest.mark.author("袁大阳")
    def test_performance_one_cx7_001(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.cx7_start_server(self.rdma_devices[0:2], self.numa_node)
            METHOD.cx7_start_client(self.rdma_devices[0:2], self.numa_node)

    @pytest.mark.author("袁大阳")
    def test_performance_two_cx7_002(self):
        assert len(self.rdma_devices) >= 4, "RDMA设备数量不足，无法执行测试用例"
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.cx7_start_server(self.rdma_devices[0:4], self.numa_node)
            METHOD.cx7_start_client(self.rdma_devices[0:4], self.numa_node)


if __name__ == '__main__':
    pytest.main(['-s',"test_link_speed_change_new.py"])