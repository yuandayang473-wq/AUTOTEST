# !/usr/bin/python3
# -*- encoding: utf-8 -*-
import os
import time

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



class TestReboot():

    config = CONFIG
    config.config = [
        {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    ]

    def _upload_current_log_to_remote(self):
        uut = self.config.config["UUT"]
        local_log = getattr(LOGGER, "log_name", "")
        print(local_log)
        if not local_log or not os.path.exists(local_log):
            LOGGER.warning(f"未找到本地日志文件，跳过上传: {local_log}")
            return

        self.remote_log = f"/root/{os.path.basename(local_log)}"
        print(self.remote_log)
        METHOD.upload_file_to_server(local_log, self.remote_log, uut["ip"], uut["username"], uut["password"])

    @pytest.fixture(scope="class", autouse=True)
    def setup_teardown(self, request):
        # setup
        LOGGER.sys(f"开始执行测试用例组:{request.cls}".center(100, "-"))
        with BASE.ssh_connect(uut=self.config.config["UUT"]):

            request.cls.test_sw_list = METHOD.get_switch_info()
            METHOD.save_data_file(request.cls.test_sw_list, 'pcie_tree_before.json')
            METHOD.upload_file_to_server('pcie_tree_before.json', 'pcie_tree_before.json',
                                     self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                     self.config.config["UUT"]["password"])
            METHOD.upload_file_to_server('Lib\\serial_check.py', 'serial_check.py', self.config.config["UUT"]["ip"],
                                         self.config.config["UUT"]["username"],
                                         self.config.config["UUT"]["password"])
            for device in request.cls.test_sw_list:
                LOGGER.info(f"{device.type}-{device.device_bdf}的CE信息：{device.aer_status['CESta']}")
                LOGGER.info(f"{device.type}-{device.device_bdf}的UCE信息：{device.aer_status['UESta']}")
                if device.current_speed == "32GT/s" and device.current_width == "16":
                    LOGGER.info(f"{device.type}-{device.device_bdf}当前链路状态正常")
                else:
                    LOGGER.warning(f"{device.type}-{device.device_bdf}当前链路状态异常，speed:{device.current_speed} width:{device.current_width}")
            BASE.execute_run('python3 serial_check.py aer')

        yield
        # teardown
        LOGGER.sys(f"结束执行测试用例组:{request.cls}".center(100, "-"))

    def test_reboot_001(self):
        ip = self.config.config["UUT"]["ip"]
        try:
            for i in range(1, 81):
                LOGGER.sys("第{}次reboot".format(i))
                with BASE.ssh_connect(uut=self.config.config["UUT"]):
                    BASE.execute_run(
                        "reboot", i_exit_code=True)
                for j in range(20):
                    SLEEP(25)
                    BASE.os_run.run("ping -n 4 {}".format(ip), i_exit_code=True)
                    if BASE.os_run.get_exit_code() == 0:
                        break
                else:
                    raise Exception("500S仍未连接")

                with BASE.ssh_connect(uut=self.config.config["UUT"]):
                    test_sw_list_after = METHOD.get_switch_info()
                    METHOD.save_data_file(test_sw_list_after, 'pcie_tree_after.json')
                    METHOD.upload_file_to_server('pcie_tree_after.json', 'pcie_tree_after.json',
                                                 self.config.config["UUT"]["ip"], self.config.config["UUT"]["username"],
                                                 self.config.config["UUT"]["password"])
                    BASE.execute_run('diff pcie_tree_before.json pcie_tree_after.json', i_exit_code=True)
                    if BASE.ssh.get_exit_code() != 0:
                        LOGGER.warning("目标SW PCIe主要信息发生变化，具体见上diff结果")

                    for device in test_sw_list_after:
                        LOGGER.info(f"{device.type}-{device.device_bdf}的CE信息：{device.aer_status['CESta']}")
                        LOGGER.info(f"{device.type}-{device.device_bdf}的UCE信息：{device.aer_status['UESta']}")
                        if device.current_speed == "32GT/s" and device.current_width == "16":
                            LOGGER.info(f"{device.type}-{device.device_bdf}当前链路状态正常")
                        else:
                            LOGGER.warning(f"{device.type}-{device.device_bdf}当前链路状态异常，speed:{device.current_speed} width:{device.current_width}")

                    BASE.execute_run('python3 serial_check.py aer')
        finally:
            # 测试步骤结束后，将本次日志上传到远端 /root 目录。
            self._upload_current_log_to_remote()
            with BASE.ssh_connect(uut=self.config.config["UUT"]):
                ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
                aer_log = f"aer_{ts}.log"
                point_log = f"point_{ts}.log"

                BASE.execute_run(f"grep -a -A 7 'aer all' {self.remote_log} >> {aer_log}")
                BASE.execute_run(f"grep -a '：DLP' {self.remote_log} >> {aer_log}")
                BASE.execute_run(f"grep -a '：RxErr' {self.remote_log} >> {aer_log}")
                BASE.execute_run(f"printf '\\n===== BADTLP =====\\n' >> {point_log}")
                BASE.execute_run(f'grep -a "BadTLP+" {self.remote_log} |grep "CE信息" >> {point_log}', i_exit_code=True)
                BASE.execute_run(f"printf '\\n===== RXERR =====\\n' >> {point_log}")
                BASE.execute_run(f'grep -a "RxErr+" {self.remote_log} |grep "CE信息" >> {point_log}', i_exit_code=True)
                BASE.execute_run(f"printf '\\n===== BADDLLP =====\\n' >> {point_log}")
                BASE.execute_run(f'grep -a "BadDLLP+" {self.remote_log} |grep "CE信息" >> {point_log}', i_exit_code=True)
                BASE.execute_run(f"printf '\\n===== SDES =====\\n' >> {point_log}")
                BASE.execute_run(f'grep -a "SDES+" {self.remote_log} |grep "UCE信息" >> {point_log}', i_exit_code=True)
                LOGGER.info(f"远端日志已生成: /root/{aer_log}, /root/{point_log}")
