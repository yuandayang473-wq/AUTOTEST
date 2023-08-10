
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
import time

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
from Lib.Request import MesSocket
from TestCases.dvt.rt.PowerCycle import PowerCycle



class Rt1StationCrossing(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "Rt1 kingkong log upload"
        self.expect = "This is cpu config check for normal case."
  
        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":self.locals["UUT"]},
            {"file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "BmcDevice.yaml", "name": "JBMC", "key":self.locals["TAIL_ADMIN_BMC"]},
        ]
    def exe(self):
        
        with self.ssh_connect(uut=self.config["UUT"]):
            jbmc_ip = self.config["JBMC"]["ip_address"]
            jbmc_user = self.config["JBMC"]["username"]
            jbmc_passwd = self.config["JBMC"]["password"]
            path = self.config["InitPath"]
            _mes = MesSocket()
            station = "LXKS_K02-2FFATP-01_1_RT1"
            sn = self.parent.globals['SN']
            starttime = self.parent.globals['start_time']
            from_format = "%Y_%m_%d_%H_%M_%S"
            to_format = "%Y-%m-%d %H:%M:%S"
            to_format_2 = "%Y%m%d%H%M%S"
            struct_time = time.strftime(from_format, time.localtime())
            time_struct = time.strptime(struct_time, from_format)
            stoptime = time.strftime(to_format, time_struct)
            time_struct = time.strptime(struct_time, from_format)
            settime = time.strftime(to_format_2, time_struct)
            kklog_name = f"{self.parent.globals['PUT']}_{self.parent.globals['RK']}_{self.parent.globals['SN']}/"
            self.parent.globals['start_time'] = stoptime
            payload = {"cmd": "ADD", "empNo": "", "terminalName": station,
                   "wo": "", "sn": sn, "csn": "", "kpsn": "", "lotNo": "", 
                   "machineNo": "", "toolingNo": "", "cavityNo": "", "result": "PASS", "defectCode": "",
                    "uut_start": starttime, "uut_stop": stoptime, 
                    "limits_version": "", "software_name": "", "software_version": ""}
            cmd = "mkdir /LogFile;mount -t cifs -o vers=2.0,username=share,password=Password@_,sec=ntlmssp,cache=none,nobrl //172.20.0.103/LogFile/Backup/Data /LogFile"
            self.execute_run(cmd, save_exit_code=True)
            self.execute_run(f'''df | grep -iE "{path['source_path']}.*/mnt"''', save_exit_code=True)
            if self.ssh.get_exit_code() != 0:
                # self.execute_run("mount -t cifs -o vers=2.0,username=Administrator,password=\`1q,sec=ntlmssp,cache=none,nobrl {path.get('source_path')} /mnt")
                self.execute_run(f"{path['mount_cmd']}")
            cmd = f'cd /mnt/kklog/{kklog_name} ; zip -r -q /LogFile/Luxshare-PPU_Kingkong_Test/{sn}{settime}.zip *.tar.xz' 
            self.execute_run(cmd)
            _mes.station_crossing(payload)
            payload = {"cmd": "ATT", "p": "GetNextTestInfo", "sn": sn}
            _mes.check_station_crossing(payload)


            
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(Rt1StationCrossing)

