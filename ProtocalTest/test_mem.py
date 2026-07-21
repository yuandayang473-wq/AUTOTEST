# !/usr/bin/python3
# -*- encoding: utf-8 -*-
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
class TestMEM:

    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]
    bdf = None
    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.sys(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            request.cls.devices = METHOD.get_switch_info()
            LOGGER.info("设备信息:{}".format(request.cls.devices))
        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))

    def test_pcie_sys_mem_005(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for device in self.devices:
                if device.class_code == "0108":
                    self.bdf = device.device_bdf
            assert self.bdf is not None, "未找到class code为0108的设备，请确认测试环境中是有NVME设备"
            nvme_name = METHOD.get_nvme_symbolic_name(self.bdf)
            stamp = int(time.time())
            size_mb = 4
            offset_mb = 64
            host_src = f"/dev/shm/test_pcie_sys_mem_005_src_{stamp}.bin"
            host_back = f"/dev/shm/test_pcie_sys_mem_005_back_{stamp}.bin"

            LOGGER.info(
                f"裸盘测试路径: nvme={nvme_name}, host_src={host_src}, host_back={host_back}, "
                f"size_mb={size_mb}, offset_mb={offset_mb}"
            )
            try:
                # 1) 在主机内存盘(/dev/shm)创建源文件
                BASE.execute_run(f"dd if=/dev/urandom of={host_src} bs=1M count={size_mb} status=none")

                # 2) host -> NVMe
                BASE.execute_run(
                    f"dd if={host_src} of={nvme_name} bs=1M seek={offset_mb} count={size_mb} conv=fsync status=none"
                )

                # 3) NVMe -> host
                BASE.execute_run(
                    f"dd if={nvme_name} of={host_back} bs=1M skip={offset_mb} count={size_mb} status=none"
                )

                src_hash = BASE.execute_run(f"sha256sum {host_src} | awk '{{print $1}}'").get_origin_data().strip()
                back_hash = BASE.execute_run(f"sha256sum {host_back} | awk '{{print $1}}'").get_origin_data().strip()

                assert src_hash == back_hash, "NVMe->host 回读后文件校验和不一致"
            finally:
                BASE.execute_run(f"rm -f {host_src} {host_back}", i_exit_code=True)

    def _get_memory_bars(self, bdf):
        bars = []
        for bar_num in range(6):
            bar_addr = METHOD.get_bar_address(bdf, bar_num, i_exit_code=True)
            if bar_addr:
                bars.append((bar_num, bar_addr))
        return bars

    def test_pcie_sys_mem_006(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.insmod_dma_driver(self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            mep_devices = [d for d in self.devices if d.type == "MEP"]
            dma_devices = [d for d in self.devices if d.type == "DMA"]
            assert mep_devices, "未发现MEP设备，无法执行PCIe_SYS_MEM_006"
            assert dma_devices, "未发现DMA设备，无法执行PCIe_SYS_MEM_006"

            for device in mep_devices:
                BASE.execute_run(f"lspci -s {device.device_bdf}")
                bars = self._get_memory_bars(device.device_bdf)
                assert bars, f"mep设备{device.device_bdf}未发现可访问Memory BAR"
                for bar_num, bar_addr in bars:
                    write_value = 0x5A5A0000 | bar_num
                    rw_detail = METHOD.devmem2_read(
                        hex(int(bar_addr, 16)),
                        width="w",
                        write_value=write_value,
                        return_detail=True,
                    )
                    write_code = rw_detail["write_exit_code"]
                    read_code = rw_detail["read_exit_code"]
                    read_value = rw_detail["read_value_int"]
                    assert write_code == 0 and read_code == 0, (
                        f"mep设备{device.device_bdf} BAR{bar_num} devmem访问失败"
                    )
                    assert read_value == write_value, (
                        f"mep设备{device.device_bdf} BAR{bar_num}数据不一致: "
                        f"write=0x{write_value:08x}, read={read_value}"
                    )
            for device in dma_devices:
                BASE.execute_run(f"lspci -s {device.device_bdf}")
                bars = self._get_memory_bars(device.device_bdf)
                assert bars, f"dma设备{device.device_bdf}未发现可访问Memory BAR"
                bar_num, bar_addr = bars[0]
                write_value = 0x5A | bar_num
                rw_detail = METHOD.devmem2_read(
                    hex(int(bar_addr, 16) + 0x120),
                    width="b",
                    write_value=write_value,
                    return_detail=True,
                )
                write_code = rw_detail["write_exit_code"]
                read_code = rw_detail["read_exit_code"]
                read_value = rw_detail["read_value_int"]
                assert write_code == 0 and read_code == 0, (
                    f"dma设备{device.device_bdf} BAR{bar_num} devmem访问失败"
                )
                assert read_value == write_value, (
                    f"dma设备{device.device_bdf} BAR{bar_num}数据不一致: "
                    f"write=0x{write_value:08x}, read={read_value}"
                )

    def test_pcie_sys_mem_011(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.insmod_dma_driver(self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            dsp_bdf = next((d.device_bdf for d in self.devices if d.type == "DSP" and d.children is not None), None)
            usp_bdf = next((d.device_bdf for d in self.devices if dsp_bdf in d.children), None)
            ep_bdf = next((d.device_bdf for d in self.devices if d.parent == dsp_bdf), None)
            dma_bdf = next((d.device_bdf for d in self.devices if d.type == "DMA"), None)
            dma_idsp_bdf = next((d.device_bdf for d in self.devices if dma_bdf in d.children), None)
            mep_bdf = next((d.device_bdf for d in self.devices if d.type == "MEP"), None)
            mep_idsp_bdf = next((d.device_bdf for d in self.devices if mep_bdf in d.children), None)
            test_list = [(dsp_bdf, ep_bdf), (usp_bdf, ep_bdf), (dma_idsp_bdf, dma_bdf), (mep_idsp_bdf, mep_bdf), (dma_bdf, dma_bdf), (mep_bdf, mep_bdf)]
            LOGGER.info(f"测试列表: {test_list}")
            for access_bdf, target_bdf in test_list:
                assert access_bdf is not None, f"未发现访问设备，无法执行PCIe_SYS_MEM_011"
                assert target_bdf is not None, f"未发现目标设备，无法执行PCIe_SYS_MEM_011"
                bars = self._get_memory_bars(target_bdf)
                assert bars, f"目标设备{target_bdf}未发现可访问Memory BAR"
                bar_num, bar_addr = bars[0]
                METHOD.clear_error_status(access_bdf)
                try:
                    METHOD.set_memory_enable(access_bdf, enable=False)
                    command_status = METHOD.get_command_enable_status(access_bdf)
                    assert command_status["memory_enable"] is False, f"访问设备{access_bdf} Memory Enable位未关闭"

                    # 只选取单个 BAR 空间执行读取校验
                    read_detail = METHOD.devmem2_read(bar_addr, width="w", return_detail=True)
                    read_code = read_detail["read_exit_code"]
                    read_hex = (read_detail["read_value_hex"] or "").lower()
                    read_blocked = read_code == 0 and read_hex in ("0xff", "0xffff", "0xffffffff")
                    assert read_blocked, (
                        f"访问设备{access_bdf}关闭使能后，目标设备{target_bdf} BAR{bar_num}读不符合预期: "
                        f"exit={read_code}, value={read_detail['read_value_hex']}"
                    )

                    error_status = METHOD.get_error_status_info(access_bdf)
                    has_ur = "UnsupReq+" in error_status.get("DevSta", "") or "UnsupReq+" in error_status.get("UESta", "")
                    assert has_ur, f"设备{access_bdf}未检测到UR错误，当前AER={error_status}"
                finally:
                    METHOD.set_memory_enable(access_bdf, enable=True)
                    METHOD.clear_error_status(access_bdf)

    def _assert_single_bar_rw_failed(self, access_bdf, case_name):
        bars = self._get_memory_bars(access_bdf)
        assert bars, f"{case_name}: 设备{access_bdf}未发现可访问Memory BAR"
        bar_num, bar_addr = bars[0]
        write_value = 0xC3C30000 | bar_num
        rw_detail = METHOD.devmem2_read(
            bar_addr,
            width="w",
            write_value=write_value,
            return_detail=True,
        )
        write_code = rw_detail["write_exit_code"]
        read_code = rw_detail["read_exit_code"]
        read_value = rw_detail["read_value_int"]
        rw_success = write_code == 0 and read_code == 0 and read_value == write_value
        assert not rw_success, (
            f"{case_name}: 读写未失败，BAR{bar_num}仍可正常访问: "
            f"write_code={write_code}, read_code={read_code}, read={rw_detail['read_value_hex']}"
        )
    @pytest.mark.env_hint("需要SW带有NTB")
    def test_pcie_sys_mem_012(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            ntb_device = next((d for d in self.devices if d.type == "NTB"), None)
            assert ntb_device is not None, "未发现NTB设备，无法执行PCIe_SYS_MEM_012"
            METHOD.insmod_ntb_driver(self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            ntb_bdf = ntb_device.device_bdf

            try:
                METHOD.set_memory_enable(ntb_bdf, enable=False)
                command_status = METHOD.get_command_enable_status(ntb_bdf)
                assert command_status["memory_enable"] is False, f"NTB设备{ntb_bdf} Memory Enable位未关闭"
                self._assert_single_bar_rw_failed(ntb_bdf, "PCIe_SYS_MEM_012")
            finally:
                METHOD.set_memory_enable(ntb_bdf, enable=True)
    @pytest.mark.env_hint("需要SW带有NTB")
    def test_pcie_sys_mem_013(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            ntb_device = next((d for d in self.devices if d.type == "NTB"), None)
            assert ntb_device is not None, "未发现NTB设备，无法执行PCIe_SYS_MEM_013"
            METHOD.insmod_ntb_driver(self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])

            ntb_idsp_bdf = ntb_device.parent
            ntb_idsp_device = next((d for d in self.devices if d.device_bdf == ntb_idsp_bdf and d.type == "NTB_IDSP"), None)
            assert ntb_idsp_device is not None, f"未发现NTB iDSP设备{ntb_idsp_bdf}，无法执行PCIe_SYS_MEM_013"

            try:
                METHOD.set_memory_enable(ntb_idsp_bdf, enable=False)
                command_status = METHOD.get_command_enable_status(ntb_idsp_bdf)
                assert command_status["memory_enable"] is False, f"NTB iDSP设备{ntb_idsp_bdf} Memory Enable位未关闭"
                self._assert_single_bar_rw_failed(ntb_device.device_bdf, "PCIe_SYS_MEM_013")
            finally:
                METHOD.set_memory_enable(ntb_idsp_bdf, enable=True)


if __name__ == '__main__':
    pytest.main(['-s',""])