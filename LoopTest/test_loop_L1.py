# !/usr/bin/python3
# -*- encoding: utf-8 -*-
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
class TestLoopL1:

    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]
    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.sys(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        # with BASE.ssh_connect(uut=self.config.config["UUT"]):
        #     request.cls.devices = METHOD.get_bdf()
        #     LOGGER.info("设备信息:{}".format(request.cls.devices))
        #     request.cls.ep_bdf = request.cls.devices["0000"][0]["eps"][0]["ep"]
        #     METHOD.upload_file_to_server('Lib\\serial_check.py', 'serial_check.py', self.config.config["UUT"]["ip"],
        #                                  self.config.config["UUT"]["username"],
        #                                  self.config.config["UUT"]["password"])
        #     request.cls.aer_info_before = METHOD.get_aer_status_info(request.cls.ep_bdf)
        #     if len(request.cls.devices["0000"]) >= 2:
        #         request.cls.ep_bdf2 = request.cls.devices["0000"][1]["eps"][0]["ep"]
        #         request.cls.aer_info_before2 = METHOD.get_aer_status_info(request.cls.ep_bdf2)
        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))
        raise Exception("测试结束，执行teardown")
        # with BASE.ssh_connect(uut=self.config.config["UUT"]):
        #     LOGGER.info("恢复ASPM状态")
        #     METHOD.ASPM_enable(self.ep_bdf, L0s=False, L1=False)
        #     if len(request.cls.devices["0000"]) >= 2:
        #         LOGGER.info("恢复ASPM状态")
        #         METHOD.ASPM_enable(self.ep_bdf2, L0s=False, L1=False)

    def test_loop_L1_001(self):
        assert 1 == 2, "测试失败，1不等于2"
        # with BASE.ssh_connect(uut=self.config.config["UUT"]):
        #     LOGGER.info("开始执行ASPM L1 enable循环测试")
        #     METHOD.ASPM_enable(self.ep_bdf, L0s=False, L1=True)
        #     if len(self.devices["0000"]) >= 2:
        #         METHOD.ASPM_enable(self.ep_bdf2, L0s=False, L1=True)
        #     BASE.execute_run("python3 serial_check.py check_l1")
        #     METHOD.ASPM_enable(self.ep_bdf, L0s=False, L1=False)
        #     aer_info_after = METHOD.get_aer_status_info(self.ep_bdf)
        #     assert aer_info_after == self.aer_info_before, "L1前后ep aer信息不同"
        #     if len(self.devices["0000"]) >= 2:
        #         METHOD.ASPM_enable(self.ep_bdf2, L0s=False, L1=False)
        #         aer_info_after2 = METHOD.get_aer_status_info(self.ep_bdf2)
        #         assert aer_info_after2 == self.aer_info_before2, "L1前后ep aer信息不同"

if __name__ == '__main__':
    pytest.main(['-s',""])