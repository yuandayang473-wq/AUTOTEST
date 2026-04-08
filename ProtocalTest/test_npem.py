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
class TestNPEM:

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
            request.cls.bdf_list = []
            request.cls.dsp_bdf_list = []
            for device in request.cls.devices:
                if device.class_code == "0108":
                    request.cls.bdf_list.append(device.device_bdf)
                    request.cls.dsp_bdf_list.append(device.parent)
            assert request.cls.bdf_list != [], "未找到class code为0108的设备，请确认测试环境中是否有支持NPEM功能的设备"
            request.cls.dsp_bdf = request.cls.dsp_bdf_list[0]
            request.cls.dsp_bdf2 = request.cls.dsp_bdf_list[1]
            request.cls.dsp_bdf3 = request.cls.dsp_bdf_list[2]
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
            LOGGER.info("恢复npem control状态")
            BASE.execute_run(f"setpci -s {request.cls.dsp_bdf} ECAP_NPEM+8.W=0000")
            BASE.execute_run(f"setpci -s {request.cls.dsp_bdf2} ECAP_NPEM+8.W=0000")
            BASE.execute_run(f"setpci -s {request.cls.dsp_bdf3} ECAP_NPEM+8.W=0000")
            devices_after = METHOD.get_switch_info()
            METHOD.save_data_file(devices_after, 'pcie_tree_after.json')
            METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                         self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json')

    def test_pcie_sys_npem_001(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            res = BASE.execute_run(f"lspci -vvvs {self.dsp_bdf}").get_origin_data()
            assert "Native PCIe Enclosure Management" in res, f"{self.dsp_bdf}lspci -vvv配置空间未找到NPEM"

    def test_pcie_sys_npem_002(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.npem_enable(self.dsp_bdf, enable=False)
            res = BASE.execute_run(f"setpci -s {self.dsp_bdf} ECAP_NPEM+8.B").get_origin_data()
            assert res[1] == "0", f"NPEM disable后ECAP_NPEM+8.B寄存器值不为0,实际值为{res[1]}"

    def test_pcie_sys_npem_003(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.npem_enable(self.dsp_bdf)
            res = BASE.execute_run(f"setpci -s {self.dsp_bdf} ECAP_NPEM+8.B").get_origin_data()
            assert res[1] == "1", f"NPEM disable后ECAP_NPEM+8.B寄存器值不为1,实际值为{res[1]}"

    def test_pcie_sys_npem_004(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            BASE.execute_run(f"setpci -s {self.dsp_bdf} ECAP_NPEM+8.B=2")
    @pytest.mark.interaction
    def test_pcie_sys_npem_005(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.npem_control(self.dsp_bdf, "OK")
            input("指示灯已设置为OK，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Locate")
            input("指示灯已设置为Locate，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Fail")
            input("指示灯已设置为Fail，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Rebuild")
            input("指示灯已设置为Rebuild，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "PFA")
            input("指示灯已设置为PFA，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Hot Spare")
            input("指示灯已设置为Hot Spare，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "A Critical Array")
            input("指示灯已设置为A Critical Array，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "A Failed Array")
            input("指示灯已设置为A Failed Array，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")

    @pytest.mark.interaction
    def test_pcie_sys_npem_006(self):
        assert len(self.bdf_list) >= 3, "本用例执行时，请确认测试环境中至少存在三个NVME设备"
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            self.bdf= self.bdf_list[0]
            self.bdf2 = self.bdf_list[1]
            self.bdf3 = self.bdf_list[2]
            nvme_name = METHOD.get_nvme_symbolic_name(self.bdf)
            nvme_name2 = METHOD.get_nvme_symbolic_name(self.bdf2)
            nvme_name3 = METHOD.get_nvme_symbolic_name(self.bdf3)
            BASE.execute_run(f"ledctl locate={nvme_name}")
            input("使用ledctl命令，查找单个块设备，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            BASE.execute_run(f"ledctl locate_off={nvme_name}")
            input("使用ledctl命令，关闭查找单个块设备，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            # BASE.execute_run(f"mdadm --create /dev/md0 --level=0 --raid-devices=2 {nvme_name} {nvme_name2}")
            # nvme = nvme_name[5:]
            # nvme2 = nvme_name2[5:]
            # BASE.execute_run(f"ledctl locate=/dev/md0 rebuild={{ /sys/block/{nvme} /sys/block/{nvme2} }}")
            # input("使用ledctl命令，查找 MD 软件 RAID 设备的磁盘，并同时为两个块设备设置重构建模式，确认是否符合预期后按回车继续执行测试用例")
            # BASE.execute_run(f"mdadm --stop /dev/md0")
            # BASE.execute_run(f"mdadm --zero-superblock {nvme_name}")
            # BASE.execute_run(f"mdadm --zero-superblock {nvme_name2}")
            BASE.execute_run(f"ledctl off={{ {nvme_name} {nvme_name2} }}")
            input("使用ledctl命令，关闭指定设备的“状态 LED”和“故障 LED”，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            BASE.execute_run(f"ledctl locate={{ {nvme_name} {nvme_name2} {nvme_name3} }}")
            input("使用ledctl命令，找到三个块设备，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")

    def test_pcie_sys_npem_007(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for i in range(10000):
                LOGGER.info("正在进行第{}轮循环".format(i + 1))
                res = BASE.execute_run(f"lspci -vvvs {self.dsp_bdf}").get_origin_data()
                assert "Native PCIe Enclosure Management" in res, f"{self.dsp_bdf}lspci -vvv配置空间未找到NPEM"

    @pytest.mark.interaction
    def test_pcie_sys_npem_008(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            for i in range(10000):
                LOGGER.info("正在进行第{}轮循环".format(i + 1))
                METHOD.npem_control(self.dsp_bdf, "OK")
                METHOD.npem_control(self.dsp_bdf, "Locate")
                METHOD.npem_control(self.dsp_bdf, "Fail")
                METHOD.npem_control(self.dsp_bdf, "Rebuild")
                METHOD.npem_control(self.dsp_bdf, "PFA")
                METHOD.npem_control(self.dsp_bdf, "Hot Spare")
                METHOD.npem_control(self.dsp_bdf, "A Critical Array")
                METHOD.npem_control(self.dsp_bdf, "A Failed Array")
            METHOD.npem_control(self.dsp_bdf, "OK")
            input("指示灯已设置为OK，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Locate")
            input("指示灯已设置为Locate，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Fail")
            input("指示灯已设置为Fail，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Rebuild")
            input("指示灯已设置为Rebuild，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "PFA")
            input("指示灯已设置为PFA，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Hot Spare")
            input("指示灯已设置为Hot Spare，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "A Critical Array")
            input("指示灯已设置为A Critical Array，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "A Failed Array")
            input("指示灯已设置为A Failed Array，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")

    @pytest.mark.interaction
    def test_pcie_sys_npem_009(self):
        assert len(self.bdf_list) >= 3, "本用例执行时，请确认测试环境中至少存在三个NVME设备"
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            self.bdf= self.bdf_list[0]
            self.bdf2 = self.bdf_list[1]
            self.bdf3 = self.bdf_list[2]
            nvme_name = METHOD.get_nvme_symbolic_name(self.bdf)
            nvme_name2 = METHOD.get_nvme_symbolic_name(self.bdf2)
            nvme_name3 = METHOD.get_nvme_symbolic_name(self.bdf3)
            for i in range(10000):
                LOGGER.info("正在进行第{}轮循环".format(i + 1))
                BASE.execute_run(f"ledctl locate={nvme_name}")
                BASE.execute_run(f"ledctl locate_off={nvme_name}")
                BASE.execute_run(f"ledctl off={{ {nvme_name} {nvme_name2} }}")
                BASE.execute_run(f"ledctl locate={{ {nvme_name} {nvme_name2} {nvme_name3} }}")
            BASE.execute_run(f"ledctl locate={nvme_name}")
            input("使用ledctl命令，查找单个块设备，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            BASE.execute_run(f"ledctl locate_off={nvme_name}")
            input("使用ledctl命令，关闭查找单个块设备，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            # BASE.execute_run(f"mdadm --create /dev/md0 --level=0 --raid-devices=2 {nvme_name} {nvme_name2}")
            # nvme = nvme_name[5:]
            # nvme2 = nvme_name2[5:]
            # BASE.execute_run(f"ledctl locate=/dev/md0 rebuild={{ /sys/block/{nvme} /sys/block/{nvme2} }}")
            # input("使用ledctl命令，查找 MD 软件 RAID 设备的磁盘，并同时为两个块设备设置重构建模式，确认是否符合预期后按回车继续执行测试用例")
            # BASE.execute_run(f"mdadm --stop /dev/md0")
            # BASE.execute_run(f"mdadm --zero-superblock {nvme_name}")
            # BASE.execute_run(f"mdadm --zero-superblock {nvme_name2}")
            BASE.execute_run(f"ledctl off={{ {nvme_name} {nvme_name2} }}")
            input("使用ledctl命令，关闭指定设备的“状态 LED”和“故障 LED”，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            BASE.execute_run(f"ledctl locate={{ {nvme_name} {nvme_name2} {nvme_name3} }}")
            input("使用ledctl命令，找到三个块设备，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")

    @pytest.mark.interaction
    def test_pcie_sys_npem_010(self):
        assert len(self.bdf_list) >= 3, "本用例执行时，请确认测试环境中至少存在三个NVME设备"
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            self.bdf= self.bdf_list[0]
            self.bdf2 = self.bdf_list[1]
            self.bdf3 = self.bdf_list[2]
            nvme_name = METHOD.get_nvme_symbolic_name(self.bdf)
            nvme_name2 = METHOD.get_nvme_symbolic_name(self.bdf2)
            nvme_name3 = METHOD.get_nvme_symbolic_name(self.bdf3)
            BASE.execute_run(f"ledctl locate={nvme_name}")
            input("使用ledctl命令，查找单个块设备，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            BASE.execute_run(f"ledctl locate_off={nvme_name}")
            input("使用ledctl命令，关闭查找单个块设备，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            BASE.execute_run(f"ledctl off={{ {nvme_name} {nvme_name2} }}")
            input("使用ledctl命令，关闭指定设备的“状态 LED”和“故障 LED”，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            BASE.execute_run(f"ledctl locate={{ {nvme_name} {nvme_name2} {nvme_name3} }}")
            input("使用ledctl命令，找到三个块设备，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")

    @pytest.mark.interaction
    def test_pcie_sys_npem_011(self):
        with BASE.ssh_connect(uut=self.config.config["UUT"]):
            METHOD.npem_control(self.dsp_bdf, "OK")
            input("指示灯已设置为OK，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Locate")
            input("指示灯已设置为Locate，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Fail")
            input("指示灯已设置为Fail，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Rebuild")
            input("指示灯已设置为Rebuild，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "PFA")
            input("指示灯已设置为PFA，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "Hot Spare")
            input("指示灯已设置为Hot Spare，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "A Critical Array")
            input("指示灯已设置为A Critical Array，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")
            METHOD.npem_control(self.dsp_bdf, "A Failed Array")
            input("指示灯已设置为A Failed Array，请观察设备指示灯状态，确认是否符合预期后按回车继续执行测试用例")


if __name__ == '__main__':
    pytest.main(['-s',""])