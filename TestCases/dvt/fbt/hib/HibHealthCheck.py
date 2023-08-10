# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   HibHealthCheck.py
@Time    :   2023/5/9
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   健康检查
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


class HibHealthCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "health"
        self.expect = "This is health check check test"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "path", "key": "InitPath"},
        ]

    def exe(self):
        path = self.config["path"]
        kingkong_path_zip = os.path.join(path["test_path"], path["kingkong"])
        kingkong_dir = os.path.join("/root", path['kingkong_dir'])
        with self.ssh_connect(uut=self.config["UUT"]):
            self.execute_run(f"rm -rf {kingkong_dir}")
            self.execute_run(f"unzip {kingkong_path_zip}")
            # cmd = "python kk.pyc -t default -m default -c ./testcase/testcase_healthcheck.yaml -d default"
            cmd = f"python {kingkong_dir}/kk.pyc -t default -m default -c {kingkong_dir}/testcase/testcase_healthcheck.yaml -d default"
            parser = self.execute_run(cmd)

            ret = parser.get_value(f"Final_Result: (PASS)")
            self.assertEqual("health check Final_Result ", ret.lower(), "pass")

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(HibHealthCheck)

