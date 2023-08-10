
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



class AtStationCrossing(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "cpu config check"
        self.expect = "This is cpu config check for normal case."
  
        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":self.locals["UUT"]},
            
            {"file": "BmcDevice.yaml", "name": "JBMC", "key":self.locals["TAIL_ADMIN_BMC"]},
        ]
    def exe(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            jbmc_ip = self.config["JBMC"]["ip_address"]
            jbmc_user = self.config["JBMC"]["username"]
            jbmc_passwd = self.config["JBMC"]["password"]
            _mes = MesSocket()
            station = "LXKS_K02-2FFATP-01_1_CT2"
            sn = self.parent.globals['SN']
            starttime = self.parent.globals['start_time']
            

            from_format = "%Y_%m_%d_%H_%M_%S"
            to_format = "%Y-%m-%d %H:%M:%S"
            struct_time = time.strftime(from_format, time.localtime())
            time_struct = time.strptime(struct_time, from_format)
            stoptime = time.strftime(to_format, time_struct)
            self.parent.globals['start_time'] = stoptime
            payload = {"cmd": "ADD", "empNo": "", "terminalName": station,
                   "wo": "", "sn": sn, "csn": "", "kpsn": "", "lotNo": "", 
                   "machineNo": "", "toolingNo": "", "cavityNo": "", "result": "PASS", "defectCode": "",
                    "uut_start": starttime, "uut_stop": stoptime, 
                    "limits_version": "", "software_name": "", "software_version": ""}
            print(payload)
            _mes.station_crossing(payload)
            payload = {"cmd": "ATT", "p": "GetNextTestInfo", "sn": sn}
            _mes.check_station_crossing(payload)
        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(AtStationCrossing)

