# !/usr/bin/python3
# -*- encoding: utf-8 -*-

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


class TestRstSbr:
    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]
    sw_targets = []

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
            request.cls.devices = METHOD.get_bdf()
            LOGGER.info("设备信息:{}".format(request.cls.devices))

            request.cls.sw_targets = []
            for sw_info in request.cls.devices.get("0000", []):
                ep_bdfs = []
                dsp_bdfs = []
                for ep_info in sw_info.get("eps", []):
                    ep_bdf = ep_info.get("ep")
                    dsp_bdf = ep_info.get("dsp")
                    if ep_bdf:
                        ep_bdfs.append(ep_bdf)
                    if dsp_bdf:
                        dsp_bdfs.append(dsp_bdf)
                request.cls.sw_targets.append({
                    "usp": sw_info.get("usp"),
                    "ep_bdfs": ep_bdfs,
                    "dsp_bdfs": dsp_bdfs,
                    "dma_idsp": sw_info.get("dma", [{}])[0].get("dsp"),
                    "mep_idsp": sw_info.get("mep", {}).get("dsp"),
                })

            assert request.cls.sw_targets, "未获取到可用SW设备"

        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))
    # @pytest.mark.xfail
    def test_pcie_sys_rst_003(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for target in self.sw_targets:
                usp_bdf = target["usp"]
                LOGGER.info("开始执行sbr usp测试")
                METHOD.sbr_set(usp_bdf)
                assert METHOD.read_config_lspci(usp_bdf) is True, "USP设备配置空间应该可读"
                for ep_bdf in target["ep_bdfs"]:
                    assert METHOD.read_config_lspci(ep_bdf) is False, f"EP设备配置空间应该不可读: {ep_bdf}"

            METHOD.pci_rescan()
            # self.devices_after = METHOD.get_switch_info()
            # METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            # METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
            #                              self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
            #                              self.config.config["UUT"]["password"])
            # BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_pcie_sys_rst_004(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for target in self.sw_targets:
                for dsp_bdf in target["dsp_bdfs"]:
                    LOGGER.info("开始执行sbr dsp测试")
                    METHOD.sbr_set(dsp_bdf)
                    assert METHOD.read_config_lspci(dsp_bdf) is True, f"DSP设备配置空间应该可读: {dsp_bdf}"

            # self.devices_after = METHOD.get_switch_info()
            # METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            # METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
            #                              self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
            #                              self.config.config["UUT"]["password"])
            # BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_pcie_sys_rst_005(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for target in self.sw_targets:
                dma_idsp_bdf = target["dma_idsp"]
                if not dma_idsp_bdf:
                    continue
                LOGGER.info("开始执行sbr dma测试")
                METHOD.sbr_set(dma_idsp_bdf)
                assert METHOD.read_config_lspci(dma_idsp_bdf) is True, f"DMA_IDSP设备配置空间应该可读: {dma_idsp_bdf}"

            # self.devices_after = METHOD.get_switch_info()
            # METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            # METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
            #                              self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
            #                              self.config.config["UUT"]["password"])
            # BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_pcie_sys_rst_006(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for target in self.sw_targets:
                mep_idsp_bdf = target["mep_idsp"]
                if not mep_idsp_bdf:
                    continue
                LOGGER.info("开始执行sbr mep测试")
                METHOD.sbr_set(mep_idsp_bdf)
                assert METHOD.read_config_lspci(mep_idsp_bdf) is True, f"MEP_IDSP设备配置空间应该可读: {mep_idsp_bdf}"

            # self.devices_after = METHOD.get_switch_info()
            # METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            # METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
            #                              self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
            #                              self.config.config["UUT"]["password"])
            # BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

if __name__ == '__main__':
    pytest.main(["-s", "test_rst_sbr.py"])
