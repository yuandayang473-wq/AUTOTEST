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

load_list = ["PPU"]


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

from Lib.Result import Pass
from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.DataBuffer import StrParser


class FuncNvmeCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "nvme"
        self.expect = "This is nvme function check test on the server"


        # rk = "RK0037030012"
        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
            # {"file": "UUT.yaml", "name": "cfg", "key": rk},
            {"file": "UUT.yaml", "name": "path", "key": "InitPath"},
        ]

    def exe(self):
        jbog_cfg = self.config["cfg"]["JBOG"]
        server_cfg = self.config['cfg']["SERVER"]
        tail_nvme_size = jbog_cfg["nvme_size"]
        tail_nvme_count = jbog_cfg["nvme_count"]
        head_nvme_size = server_cfg.get("nvme_size", "NA")
        head_nvme_count = server_cfg.get("nvme_count", 0)

        if tail_nvme_count == "NA":
            tail_nvme_count = 0

        if head_nvme_count == "NA":
            head_nvme_count = 0
        count = 0

        if tail_nvme_size == "NA" and head_nvme_size == "NA":
            return Pass(self)

        with self.ssh_connect(uut=self.config["UUT"]):
            self.step(1, "get nvme info")
            parser = self.execute_run(f"{self.config['path']['nvme_tool']} list")
            nvmes = parser.filter_list(r"(/dev/nvme.*)")
            for nvme in nvmes:
                p1 = StrParser(nvme)
                l = p1.split(r"[ ]+")
                cur_nvme_size = l[6]
                cur_nvme_unit = l[7]

                if cur_nvme_size in tail_nvme_size:
                    self.assertIn(f"{l[0]} size", tail_nvme_size, cur_nvme_size + cur_nvme_unit)
                elif cur_nvme_size in head_nvme_size:
                    self.assertIn(f"{l[0]} size", head_nvme_size, cur_nvme_size + cur_nvme_unit)
                count += 1

            self.assertEqual("nvme count", count, tail_nvme_count + head_nvme_count)

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(FuncNvmeCheck)

