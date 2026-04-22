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
class TestLoopRetrain:

    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]
    ep_dsp_pairs = []
    aer_info_before = {}

    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.sys(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            request.cls.devices = METHOD.get_bdf()
            LOGGER.info("设备信息:{}".format(request.cls.devices))
            METHOD.upload_file_to_server('Lib\\serial_check.py', 'serial_check.py', self.config.config["UUT"]["ip"],
                                         self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])

            request.cls.ep_dsp_pairs = []
            for sw_info in request.cls.devices.get("0000", []):
                for ep_info in sw_info.get("eps", []):
                    ep_bdf = ep_info.get("ep")
                    dsp_bdf = ep_info.get("dsp")
                    if ep_bdf and dsp_bdf:
                        request.cls.ep_dsp_pairs.append((ep_bdf, dsp_bdf))

            assert request.cls.ep_dsp_pairs, "未获取到可用EP/DSP设备"

            request.cls.aer_info_before = {}
            for ep_bdf, _ in request.cls.ep_dsp_pairs:
                request.cls.aer_info_before[ep_bdf] = METHOD.get_aer_status_info(ep_bdf)
        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))

    def test_loop_retrain_001(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            LOGGER.info("开始执行Retrain循环测试")
            for _, dsp_bdf in self.ep_dsp_pairs:
                METHOD.link_retrain(dsp_bdf)

            for ep_bdf, _ in self.ep_dsp_pairs:
                aer_info_after = METHOD.get_aer_status_info(ep_bdf)
                assert aer_info_after == self.aer_info_before[ep_bdf], f"retrain前后ep aer信息不同: {ep_bdf}"


if __name__ == '__main__':
    pytest.main(['-s',""])