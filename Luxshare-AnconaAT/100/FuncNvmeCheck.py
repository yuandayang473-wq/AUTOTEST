# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncNvmeCheck.py
@Time    :   2023/5/8
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/Memory测试  （机头）
'''
import os
import sys

load_list = ["LuxScript"]


def load_package(path):
    parent_folder = os.path.dirname(path)
    for dirname in os.listdir(parent_folder):
        if dirname in load_list:
            sys.path.append(os.path.join(parent_folder, dirname))
            load_list.pop(load_list.index(dirname))
        if not load_list:
            return None
    else:
        return load_package(parent_folder)


load_package(os.path.abspath(__file__))

from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Constant import ErrorCode
from Utils.Init import load_mes_info


class FuncNvmeCheck(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "nvme"
        self.expect = "This is nvme function check test on the server"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "Luxshare-AnconaAT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "Luxshare-AnconaAT/100/Config", "file": "UUT.yaml", "name": "nvme", "key": "tools/ancoan/fw/nvmefw"},
            {"folder": "Luxshare-AnconaAT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.mes_info["info"]["rk"]},
        ]

    def exe(self):
        jbog_cfg = self.config["cfg"]["JBOG"]
        server_cfg = self.config['cfg']["SERVER"]

        head_nvme_type = server_cfg.get("nvme_type", "NA")
        tail_nvme_type = jbog_cfg.get("nvme_type", "NA")

        nvme = self.config["nvme"]
        data = {}
        with self.ssh_connect(uut=self.config["UUT"]):
            if head_nvme_type != "NA":
                if "intel" in head_nvme_type.lower():
                    head_key_word = "intel"
                    head_nvme_ver = self.config["FwVsersion"]["nvme_ver"]
                elif "samsung" in head_nvme_type.lower():
                    head_key_word = "samsung"
                    head_nvme_ver = self.config["FwVsersion"]["samsung_ver"]
                data[head_key_word] = head_nvme_ver

            if tail_nvme_type != "NA":
                if "intel" in tail_nvme_type.lower():
                    tail_key_word = "intel"
                    tail_nvme_ver = self.config["FwVsersion"]["nvme_ver"]
                elif "samsung" in tail_nvme_type.lower():
                    tail_key_word = "samsung"
                    tail_nvme_ver = self.config["FwVsersion"]["samsung_ver"]

                data[tail_key_word] = tail_nvme_ver

            for key_word, nvme_type in data.items():
                parser = self.execute_run(
                    f"{nvme['tool']} list | grep -i {key_word} | " + '''awk '{print $1 "-" $NF}' | xargs ''')
                nvme_list = parser.get_origin_data().split()

                for nvme in nvme_list:
                    self.assertEqual(ErrorCode.FFFFFFFF, f"check device {nvme.split('-')[0]} fw version",
                                     nvme.split('-')[1].strip(), nvme_type.strip())


if __name__ == '__main__':
    runner.single_runner(FuncNvmeCheck)
