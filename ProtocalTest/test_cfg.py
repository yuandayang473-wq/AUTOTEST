# !/usr/bin/python3
# -*- encoding: utf-8 -*-
import pytest

from Lib import *


class TestCFG:

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
			assert request.cls.devices, "未发现SW相关设备，无法执行CFG测试"
		yield
		# teardown
		LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))


	def test_pcie_sys_cfg_001(self):
		with BASE.ssh_connect(uut=self.config.config["UUT"]):
			target_types = ["USP", "DSP", "DMA", "MEP"]
			targets = METHOD.get_devices_by_types(self.devices, target_types)
			assert targets, "未发现USP/DSP/DMA/MEP设备，无法执行PCIe_SYS_CFG_001"

			for target_type in target_types:
				type_devices = [d for d in targets if d.type == target_type]
				assert type_devices, f"未发现{target_type}设备，无法覆盖PCIe_SYS_CFG_001"
				for device in type_devices:
					assert METHOD.read_config_lspci(device.device_bdf) is True, f"{device.device_bdf}设备配置空间应该可读"

	def test_pcie_sys_cfg_002(self):
		with BASE.ssh_connect(uut=self.config.config["UUT"]):
			ep_devices = METHOD.get_devices_by_types(self.devices, ["EP"])
			assert ep_devices, "未发现EP设备，无法执行PCIe_SYS_CFG_002"
			for device in ep_devices:
				assert METHOD.read_config_lspci(device.device_bdf) is True, f"{device.device_bdf}设备配置空间应该可读"


if __name__ == '__main__':
	pytest.main(['-s', ""])

