# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   HealthCheck.py
@Time    :   2023/5/9
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   健康检查
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


class HealthCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "health"
        self.expect = "This is health check check test"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "kingkong_path",
             "key": "tools/ancoan/kingkong"},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "kingkong_info",
             "key": "tools.ancoan.kingkong"},
        ]

    @load_mes_info
    def exe(self):
        http_server_url = self.mes_info["info"]["http_server_url"]
        _kingkong = os.path.join(http_server_url,
                                 f"LuxScript/tools/ancoan/kingkong/{self.config['kingkong_info']['kingkong']}")

        self.wget(_kingkong)

        kingkong_path_zip = self.config["kingkong_path"]["kingkong"]
        kingkong_dir = os.path.join("/root", self.config["kingkong_info"]["kingkong_name"])

        self.os_run.run(f"rm -rf {kingkong_dir}")
        self.os_run.run(f"unzip -d /root/ {kingkong_path_zip}")
        # cmd = f"python {king_king_dir}/kk.pyc -t default -m default -c {king_king_dir}/testcase/testcase_healthcheck.yaml -d default"
        # parser = self.os_run.run(cmd)
        #
        # ret = parser.get_value(f"Final_Result: (PASS)")
        # self.assertEqual(ErrorCode.FFFFFFFF, "health check Final_Result ", ret.lower(), "pass")

        with self.ssh_connect(uut=self.config["UUT"]):
            # cmd = "python kk.pyc -t default -m default -c ./testcase/testcase_healthcheck.yaml -d default"
            cmd = f"python {kingkong_dir}/kk.pyc -t default -m default -c {kingkong_dir}/testcase/testcase_healthcheck.yaml -d default"
            parser = self.execute_run(cmd)

            ret = parser.get_value(f"Final_Result: (PASS)")
            self.assertEqual(ErrorCode.FFFFFFFF, "health check Final_Result ", ret.lower(), "pass")


if __name__ == '__main__':
    runner.single_runner(HealthCheck)
