# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   NvmeFwUpdate.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
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


class NvmeFwUpdate(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "nvme fw check"
        self.expect = "This is nvme fw check for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": self.locals["UUT"]},
            {"file": "BmcDevice.yaml", "name": "BMC", "key": self.locals["TAIL_ADMIN_BMC"]},
            {"file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]

    def exe(self):
        target_nvme_ver = self.config["FwVsersion"]["nvme_ver"]
        path = self.config["InitPath"]
        with self.ssh_connect(uut=self.config["UUT"]):
            # parser = self.execute_run(f"chmod +x {path.get('nvme_tool')} && {path.get('nvme_tool')} list | grep -i intel | " + '''awk '{print $1 "-" $NF}' | xargs ''')
            parser = self.execute_run(f"chmod +x {path.get('nvme_tool')} && {path.get('nvme_tool')} list | grep -i 'INTEL' | " + '''awk '{print $1 "-" $NF}' | xargs ''')

            nvme_list = parser.get_origin_data().split()
            for nvme in nvme_list:
                if nvme.split('-')[1] != target_nvme_ver:
                    parser = self.execute_run(f"{path.get('nvme_tool')} fw-download {nvme.split('-')[0]} -f {path.get('nvme_fw')}")
                    parser = self.execute_run(f"{path.get('nvme_tool')} fw-activate {nvme.split('-')[0]} -s 0 -a 3")
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(NvmeFwUpdate)

