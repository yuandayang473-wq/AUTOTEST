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
class TestPM:

    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]
    sw_targets = []
    ep_bdfs = []
    dsp_bdfs = []
    usp_bdfs = []

    def _save_after_and_diff(self):
        pass
        # self.devices_after = METHOD.get_switch_info()
        # METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
        # METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
        #                              self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
        #                              self.config.config["UUT"]["password"])
        # BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.sys(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            request.cls.devices_before = METHOD.get_switch_info()
            LOGGER.info("设备信息:{}".format(request.cls.devices_before))
            METHOD.save_data_file(request.cls.devices_before, 'pcie_tree_before.json')
            METHOD.upload_file_to_server('pcie_tree_before.json', 'pcie_tree_before.json',
                                     self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                     self.config.config["UUT"]["password"])

            request.cls.devices = METHOD.get_bdf()
            LOGGER.info("设备信息:{}".format(request.cls.devices))
            request.cls.sw_targets = []
            request.cls.ep_bdfs = []
            request.cls.dsp_bdfs = []
            request.cls.usp_bdfs = []
            for sw_info in request.cls.devices.get("0000", []):
                eps = []
                for ep_info in sw_info.get("eps", []):
                    ep_bdf = ep_info.get("ep")
                    dsp_bdf = ep_info.get("dsp")
                    if ep_bdf and dsp_bdf:
                        eps.append((ep_bdf, dsp_bdf))
                        request.cls.ep_bdfs.append(ep_bdf)
                        request.cls.dsp_bdfs.append(dsp_bdf)
                usp_bdf = sw_info.get("usp")
                if usp_bdf:
                    request.cls.usp_bdfs.append(usp_bdf)
                request.cls.sw_targets.append({"usp": usp_bdf, "eps": eps})

            assert request.cls.ep_bdfs, "未获取到可用EP设备"
            METHOD.upload_file_to_server('Lib\\serial_check.py', 'serial_check.py', self.config.config["UUT"]["ip"],
                                     self.config.config["UUT"]["username"],
                                     self.config.config["UUT"]["password"])
        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            LOGGER.info("恢复D0状态")
            for usp_bdf in self.usp_bdfs:
                METHOD.set_power_state(usp_bdf, "D0")
            for dsp_bdf in self.dsp_bdfs:
                METHOD.set_power_state(dsp_bdf, "D0")
            for ep_bdf in self.ep_bdfs:
                METHOD.set_power_state(ep_bdf, "D0")

    def test_pcie_sys_pm_001(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for usp_bdf in self.usp_bdfs:
                cap = METHOD.get_pm_suport_pme_states(usp_bdf)
                assert cap == ["D0", "D3hot"], "USP设备PME支持的电源状态应该是D0和D3hot"
                BASE.execute_run('lspci -s {} -vvv | grep " D1- "'.format(usp_bdf))
            for dsp_bdf in self.dsp_bdfs:
                cap = METHOD.get_pm_suport_pme_states(dsp_bdf)
                assert cap == ["D0", "D3hot"], "DSP设备PME支持的电源状态应该是D0和D3hot"
                BASE.execute_run('lspci -s {} -vvv | grep " D2- "'.format(dsp_bdf))

    def test_pcie_sys_pm_002(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for usp_bdf in self.usp_bdfs:
                METHOD.PME_enable(usp_bdf)
                BASE.execute_run('lspci -s {} -vvv | grep "PME-Enable+"'.format(usp_bdf))
                METHOD.PME_enable(usp_bdf, PME=False)
            for dsp_bdf in self.dsp_bdfs:
                METHOD.PME_enable(dsp_bdf)
                BASE.execute_run('lspci -s {} -vvv | grep "PME-Enable+"'.format(dsp_bdf))
                METHOD.PME_enable(dsp_bdf, PME=False)

    # @pytest.mark.env_hint("需要特定具备ASPM能力的FW版本")
    # def test_pcie_sys_pm_004(self):
    #     pass

    def test_pcie_sys_pm_012(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for ep_bdf in self.ep_bdfs:
                METHOD.set_power_state(ep_bdf, "D0")
                SLEEP(2)
                assert METHOD.get_pm_state(ep_bdf) == "D0", f"EP设备应该处于D0状态: {ep_bdf}"
            self._save_after_and_diff()

    @pytest.mark.env_hint("需要特定具备ASPM能力的FW版本，且环境中只具备WD/三星金手指盘（支持ASPM L1）")
    def test_pcie_sys_pm_014(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for device in self.devices_before:
                if device.type == "EP":
                    METHOD.set_power_state(device.device_bdf, "D3hot")
            BASE.execute_run('python3 serial_check.py check_l1')
            for device in self.devices_before:
                if device.type == "EP":
                    METHOD.set_power_state(device.device_bdf, "D0")
            self._save_after_and_diff()

    def test_pcie_sys_pm_015(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for ep_bdf in self.ep_bdfs:
                METHOD.set_power_state(ep_bdf, "D3hot")
                SLEEP(2)
                bar = METHOD.get_bar_address(ep_bdf)
                res = METHOD.devmem2_read(bar, width="b", return_detail=True)["read_value_hex"]
                assert res == "0xFF", f"EP设备BAR地址应该不可访问，读出值为0xFF: {ep_bdf}"
                METHOD.set_power_state(ep_bdf, "D0")

            self.devices_after = METHOD.get_switch_info()
            for device in self.devices_after:
                if device.device_bdf in self.ep_bdfs:
                    error_status = device.error_status["DevSta"]
                    assert "UnsupReq+" in error_status, f"EP设备在D3hot状态下应该产生Unsupported Request错误: {device.device_bdf}"

            METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            for ep_bdf in self.ep_bdfs:
                METHOD.clear_error_status(ep_bdf)

    def test_pcie_sys_pm_016(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for dsp_bdf in self.dsp_bdfs:
                METHOD.set_power_state(dsp_bdf, "D3hot")
                SLEEP(4)
                assert METHOD.read_config_lspci(dsp_bdf) is True, f"DSP设备配置空间应该可读: {dsp_bdf}"
                METHOD.set_power_state(dsp_bdf, "D0")

            SLEEP(2)
            for usp_bdf in self.usp_bdfs:
                METHOD.set_power_state(usp_bdf, "D3hot")
                SLEEP(4)
                assert METHOD.read_config_lspci(usp_bdf) is True, f"USP设备配置空间应该可读: {usp_bdf}"
                METHOD.set_power_state(usp_bdf, "D0")

            self._save_after_and_diff()

    def test_pcie_sys_pm_017(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for target in self.sw_targets:
                usp_bdf = target["usp"]
                METHOD.set_power_state(usp_bdf, "D3hot")
                SLEEP(4)
                for _, dsp_bdf in target["eps"]:
                    assert METHOD.read_config_lspci(dsp_bdf) is False, f"DSP设备配置空间应该不可读: {dsp_bdf}"
                METHOD.set_power_state(usp_bdf, "D0")
            self._save_after_and_diff()

    def test_pcie_sys_pm_018(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for ep_bdf in self.ep_bdfs:
                METHOD.set_power_state(ep_bdf, "D3hot")
                SLEEP(4)
                assert METHOD.read_config_lspci(ep_bdf) is True, f"EP设备配置空间应该可读: {ep_bdf}"
                METHOD.set_power_state(ep_bdf, "D0")
            self._save_after_and_diff()


if __name__ == '__main__':
    pytest.main(['-s',"test_D3hot_loop.py"])