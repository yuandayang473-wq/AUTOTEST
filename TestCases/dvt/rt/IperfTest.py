
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

from Lib.Result import Pass, Fail
from Lib.Template import TempItem
from Lib.Runner import runner


class IperfTest(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "iperf test"
        self.expect = "This is iperf test for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "UUT.yaml", "name": "Iperf", "key": "Iperf"},{"file": "BmcDevice.yaml", "name": "JBMC", "key":self.locals["TAIL_TAOBAO_BMC"]},
        ]

    def exe(self):
        server_num = self.locals["PUT"].split("T")[-1]
        path = self.config["InitPath"]
        
        with self.ssh_connect(uut=self.config["UUT"]):
            mount_path = self.config["InitPath"]['mount_path']
            work_path = self.config["InitPath"]['test_path']
            iperf_rpm_file = self.config["Iperf"]['iperftool']
            iperf_script_file = self.config["Iperf"]['iperfscript']
            self.execute_run(f'''df | grep -iE "{path['source_path']}.*/mnt"''', save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                # self.execute_run("mount -t cifs -o vers=2.0,username=Administrator,password=\`1q,sec=ntlmssp,cache=none,nobrl {path.get('source_path')} /mnt")
                self.execute_run(f"{path['mount_cmd']}")
            self.execute_run(f"ls {path.get('fw_path')}", save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                #  创建文件加
                self.execute_run(f"mkdir -p {path.get('fw_path')}")
            self.execute_run(f"ls {path.get('fru_path')}", save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
            #  创建文件加
                self.execute_run(f"mkdir -p {path.get('fru_path')}")
        # self.execute_run(f"rm -rf {path.get('fw_path')}*")
            # self.execute_run(f"rm -rf {path.get('fru_path')}*")
            cmd = "mkdir /LogFile;mount -t cifs -o vers=2.0,username=share,password=Password@_,sec=ntlmssp,cache=none,nobrl //172.20.0.103/LogFile/Backup/Data /LogFile"
            self.execute_run(cmd, save_exit_code=True, i_exit_code=True)
            self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('aliaom_driver')} {path.get('test_path')}")
            self.execute_run(f"cp -rf {path['fw_source_path']} {path.get('fw_path')}")
            self.execute_run(f"cp -rf {path['mount_path']}kingkong/{path['kingkong']} {path.get('test_path')}")
            self.execute_run(f"cp -rf /mnt/fru/* {path.get('fru_path')}")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('test_path')}{path.get('aliaom_driver')}")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}mft-4.20.1-14.x86_64.rpm")
            self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}sshpass-1.09-4.el8.x86_64.rpm")
            self.execute_run("chmod -R 777 /opt/Alioam/")
            self.execute_run(f"cp -rf {mount_path}{iperf_rpm_file} {work_path}")
            self.execute_run(f"cp -rf {mount_path}{iperf_script_file} {work_path}")
            self.execute_run(f"rpm -ivh --nodeps --force {work_path}{iperf_rpm_file}")
            for i in range(10):
                try:
                    self.execute_run(f"python3 {work_path}{iperf_script_file} -rt 3600 -LOOP", cmd_timeout= 6000)
                    break
                except Exception as e :
                    self.logger.error(f'{e}')
            infos = self.execute_run(f"cat {work_path}reports/iperf/iperf*client.log |grep SUM").data.splitlines()
            for info in infos:
                check_info = info.split()[-2]
                check_info = eval(check_info)
                if check_info < 10 :
                    self.logger.error(f'find iperf Gbits/sec < 10 : {check_info}')
                    return Fail(self)
            self.execute_run(f"mv {work_path}reports/iperf/ {mount_path}iperf_log/{server_num}_iperf")
            # self.assertEqual(f"clear Server bmc sel log", int(1), len(count))
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(IperfTest)

