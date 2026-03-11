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
class TestPMD3Hot:

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
            for device in request.cls.devices:
                if device.type == 'DSP' and len(device.children) != 0:
                    request.cls.dsp_bdf = device.device_bdf
                if device.type == 'EP':
                    request.cls.ep_bdf = device.device_bdf
                if device.type == 'USP':
                    request.cls.usp_bdf = device.device_bdf
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
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            LOGGER.info("恢复D0状态")
            METHOD.set_power_state(self.usp_bdf, "D0")
            METHOD.set_power_state(self.dsp_bdf, "D0")
            METHOD.set_power_state(self.ep_bdf, "D0")


    def test_sys_pm_001(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            cap = METHOD.get_pm_suport_pme_states(self.usp_bdf)
            assert cap == ["D0", "D3hot"], "USP设备PME支持的电源状态应该是D0和D3hot"
            cap = METHOD.get_pm_suport_pme_states(self.dsp_bdf)
            assert cap == ["D0", "D3hot"], "DSP设备PME支持的电源状态应该是D0和D3hot"
            BASE.execute_run('lspci -s {} -vvv | grep " D1- "'.format(self.usp_bdf))
            BASE.execute_run('lspci -s {} -vvv | grep " D2- "'.format(self.dsp_bdf))

    def test_sys_pm_002(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.PME_enable(self.usp_bdf)
            METHOD.PME_enable(self.dsp_bdf)
            BASE.execute_run('lspci -s {} -vvv | grep "PME-Enable+"'.format(self.usp_bdf))
            BASE.execute_run('lspci -s {} -vvv | grep "PME-Enable+"'.format(self.dsp_bdf))
            METHOD.PME_enable(self.usp_bdf, PME=False)
            METHOD.PME_enable(self.dsp_bdf, PME=False)

    def test_sys_pm_012(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.set_power_state(self.ep_bdf, "D0")
            SLEEP(2)
            assert METHOD.get_pm_state(self.ep_bdf) == "D0", "EP设备应该处于D0状态"
            BASE.execute_run('python3 serial_check.py aer')
            self.devices_after = METHOD.get_switch_info()
            METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                         self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_sys_pm_013(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            list_ep = []
            for device in self.devices:
                if device.type == 'EP':
                    list_ep.append(device)
            assert len(list_ep) == 1, "本用例自动化执行必须有且仅有一个EP设备"
            cap = METHOD.get_pm_suport_pme_states(self.ep_bdf)
            METHOD.set_power_state(self.ep_bdf, "D1")
            SLEEP(2)
            if "D1" in cap:
                assert METHOD.get_pm_state(self.ep_bdf) == "D1", "EP设备应该处于D1状态"
                BASE.execute_run('python3 serial_check.py check_l1')
                METHOD.set_power_state(self.ep_bdf, "D0")
            else:
                assert METHOD.get_pm_state(self.ep_bdf) == "D0", "EP设备应该处于D0状态，因为不支持D1"
            METHOD.set_power_state(self.ep_bdf, "D2")
            SLEEP(2)
            if "D2" in cap:
                assert METHOD.get_pm_state(self.ep_bdf) == "D2", "EP设备应该处于D2状态"
                BASE.execute_run('python3 serial_check.py check_l1')
                METHOD.set_power_state(self.ep_bdf, "D0")
            else:
                assert METHOD.get_pm_state(self.ep_bdf) == "D0", "EP设备应该处于D0状态，因为不支持D2"
            BASE.execute_run('python3 serial_check.py aer')
            self.devices_after = METHOD.get_switch_info()
            METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                         self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_sys_pm_014(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            list_ep = []
            for device in self.devices:
                if device.type == 'EP':
                    list_ep.append(device)
            assert len(list_ep) == 1, "本用例自动化执行必须有且仅有一个EP设备"
            METHOD.set_power_state(self.ep_bdf, "D3hot")
            BASE.execute_run('python3 serial_check.py check_l1')
            METHOD.set_power_state(self.ep_bdf, "D0")
            BASE.execute_run('python3 serial_check.py aer')
            self.devices_after = METHOD.get_switch_info()
            METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                         self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_sys_pm_015(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.set_power_state(self.ep_bdf, "D3hot")
            SLEEP(2)
            bar = METHOD.get_bar_address(self.ep_bdf)
            res = METHOD.devmem2_read(bar)
            assert res == "0xFF", "EP设备BAR地址应该不可访问，读出值为0xFF"
            METHOD.set_power_state(self.ep_bdf, "D0")
            BASE.execute_run('python3 serial_check.py aer')
            self.devices_after = METHOD.get_switch_info()
            for device in self.devices_after:
                if device.device_bdf == self.ep_bdf:
                    aer_status = device.aer_status["DevSta"]
                    assert "UnsupReq+" in aer_status, "EP设备在D3hot状态下应该产生Unsupported Request错误"
            METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            METHOD.clear_aer_status(self.ep_bdf)

    def test_sys_pm_016(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.set_power_state(self.dsp_bdf, "D3hot")
            SLEEP(4)
            assert METHOD.read_config_lspci(self.dsp_bdf) is True, "DSP设备配置空间应该可读"
            METHOD.set_power_state(self.dsp_bdf, "D0")
            SLEEP(2)
            METHOD.set_power_state(self.usp_bdf, "D3hot")
            SLEEP(4)
            assert METHOD.read_config_lspci(self.usp_bdf) is True, "USP设备配置空间应该可读"
            METHOD.set_power_state(self.usp_bdf, "D0")
            SLEEP(2)
            BASE.execute_run('python3 serial_check.py aer')
            self.devices_after = METHOD.get_switch_info()
            METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                         self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_sys_pm_017(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.set_power_state(self.usp_bdf, "D3hot")
            SLEEP(4)
            assert METHOD.read_config_lspci(self.dsp_bdf) is False, "DSP设备配置空间应该不可读"
            METHOD.set_power_state(self.usp_bdf, "D0")
            SLEEP(2)
            BASE.execute_run('python3 serial_check.py aer')
            self.devices_after = METHOD.get_switch_info()
            METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                         self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_sys_pm_018(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.set_power_state(self.ep_bdf, "D3hot")
            SLEEP(4)
            assert METHOD.read_config_lspci(self.ep_bdf) is True, "EP设备配置空间应该可读"
            METHOD.set_power_state(self.ep_bdf, "D0")
            SLEEP(2)
            BASE.execute_run('python3 serial_check.py aer')
            self.devices_after = METHOD.get_switch_info()
            METHOD.save_data_file(self.devices_after, 'pcie_tree_after.json')
            METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                         self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')


if __name__ == '__main__':
    pytest.main(['-s',"test_D3hot_loop.py"])