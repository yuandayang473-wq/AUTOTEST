
# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Harvey
@Software:   TestCase
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
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

from Lib.Result import Pass, Fail
from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Init import load_mes_info

class IperfTest(TempItem):
    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "iperf test"
        self.expect = "This is iperf test for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
        ]

    def exe(self):
        http_server_url = self.mes_info["info"]["http_server_url"]
        _iperf_rpm = os.path.join(http_server_url, "LuxScript/tools/ancoan/rpm/iperf-2.1.6-2.el8.x86_64.rpm")
        work_path = os.path.dirname(self.root_path)
        self.os_run.run(f"cd {work_path};wget -t 5 -T 60 -r -np -nH -R index.html {_iperf_rpm}")
        iperf_tool = f'{work_path}/LuxScript/Luxshare-AncoanRT/100/IperfLoopTool.py'
        log_path = f'{work_path}/LuxScript/Luxshare-AncoanRT/100/'
        self.os_run.run(f"rpm -ivh --nodeps --force {work_path}/LuxScript/tools/ancoan/rpm/iperf-2.1.6-2.el8.x86_64.rpm")
        with self.ssh_connect(uut=self.config["UUT"]):
            for i in range(10):
                try:
                    self.execute_run(f"python3 {iperf_tool} -rt 3600 ", cmd_timeout= 6000)
                    break
                except Exception as e :
                    self.logger.error(f'{e}')
            infos = self.execute_run(f"cat {log_path}reports/iperf/iperf*client.log |grep SUM").data.splitlines()
            for info in infos:
                check_info = info.split()[-2]
                check_info = eval(check_info)
                if check_info < 10 :
                    self.logger.error(f'find iperf Gbits/sec < 10 : {check_info}')
                    return Fail(self)
            # self.execute_run(f"mv {work_path}reports/iperf/ {mount_path}iperf_log/{server_num}_iperf")
            # self.assertEqual(f"clear Server bmc sel log", int(1), len(count))
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(IperfTest)

