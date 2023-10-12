
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
import re
import os
import sys
import time
from json import dumps
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

from Lib.Runner import runner
from Lib.Request import MesSocket
from Utils.Constant import ErrorCode
from Lib.Login import ApcConnect
from Lib.Template import TempItem
from Utils.Init import load_mes_info


class DcPowerCycleCheck(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "DcPowerCycleCheck"
        self.expect = "This is DcPowerCycleCheck for normal case."

        self.config = [
            {"folder": "Luxshare-AncoanRT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
            {"folder": "Luxshare-AncoanRT/100/Config", "file": "UUT.yaml", "name": "kkpath", "key": "tools/ancoan/kingkong"},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": "BMC_01"},


        ]
    def check_gpu_monitor(self, count):
        for i in range(count):
            cmd = f"ppudbg --device {i} --time 1 --monitor | grep -A 17 CE_IDX "
            output = self.execute_run(cmd).data
            info = output.splitlines()
            na_count = 0
            for line in info[1:-2]:
                self.logger.info(line)
                info_list = line.split()
                for x in range(1,len(info_list)):
                    if info_list[x] == "N/A":
                        self.logger.error(f"check gpu device {i} monitor is fail ")
                        raise Exception(f"check gpu device {i} monitor is fail ")


    def check_gpu_lspci(self, count):
        cmd = 'lspci |grep -i 6001 |cut -d " " -f1 |xargs -I {} lspci -s {} -vvv |grep -iE "6001|LnkSta:|CESta|UESta"'
        output = self.execute_run(cmd).data
        info = re.findall('32GT.*16', output , re.I)
        self.logger.info(info)
        if len(info) != count:
            self.logger.error(f"check gpu lspci LnkSta is fail ")
            raise Exception(f"check gpu lspci LnkSta is fail ")

        re_gx = "DLP- SDES- TLP- FCP- CmpltTO- CmpltAbrt- UnxCmplt- RxOF- MalfTLP- ECRC- UnsupReq- ACSViol-"
        info = re.findall(re_gx, output , re.I)
        if len(info) != count:
            self.logger.error(f"check gpu lspci UESta is fail ")
            raise Exception(f"check gpu lspci UESta is fail ")

        re_gx = "RxErr- BadTLP- BadDLLP- Rollover- Timeout-"
        info = re.findall(re_gx, output , re.I)
        if  len(info) != count:
            self.logger.error(f"check gpu lspci CESta is fail ")
            raise Exception(f"check gpu lspci CESta is fail ")

    def check_gpu_icn(self, count):
        for i in range(count):
            cmd = f'ppudbg --device {i}  --time 1 --monitor icn'
            output = self.execute_run(cmd).data
            output_list = output.splitlines()
            for line in output_list:
                # print(line)
                if "Link" in line:
                    info = line.split()[4]
                    if info != "0" :
                        self.logger.error(f"check device {i}  gpu icn info is fail ")
                        raise Exception(f"check device {i}  gpu icn info is fail ")

    def check_gpu_micnop_prbs(self, count ):
        cmd = "ppudbg --micnop prbs 1 time 300"
        output = self.execute_run(cmd).data
        info = re.findall('test pass', output , re.I)
        if  len(info) != count:
            self.logger.error(f"check gpu micnop prbs info is fail ")
            raise Exception(f"check gpu micnop prbs info is fail ")

    def check_gpu_micnop_stat(self, count):
        check_list = ['p', '0', '3', '4', '5']
        for i in range(count):
            for x in check_list:
                cmd = f"ppudbg --device {i} --micnop stat {x}"
                output = self.execute_run(cmd).data
                info = re.findall('Link Status.*', output , re.I)[0]
                if  'Up' not in  info:
                    self.logger.error(f"check device {i} gpu micnop stat {x} info is fail ")
                    raise Exception(f"check device {i} gpu micnop stat {x} info is fail ")

    def check_gpu_mpmbop_info(self, count, mode):
        if mode == 0:
            dict_list = [{'name':'0x00', "value":"0", "location":1}, {'name':'0x20', "value":"20", "location":1}]
        elif mode == 1:
            dict_list = [{'name':'0x00', "value":"0", "location":1}, {'name':'0x20', "value":"29", "location":10},
                           {'name':'0x20', "value":"2b", "location":12}, {'name':'0x50', "value":"5c", "location":13},
                           {'name':'0x50', "value":"5e", "location":15}]
        for i in range(count):
            cmd = f"ppudbg --device {i} --mpmbop info {mode}"
            output = self.execute_run(cmd).data
            for dict_key in dict_list:
                info = re.findall(f'{dict_key["name"]}.*', output , re.I)[0]
                checkinfo = info.split()[dict_key["location"]]
                if  checkinfo !=  dict_key['value']:
                    self.logger.error(f"check device {i} gpu mpmbop info {mode} {dict_key['name']} is fail ")
                    raise Exception(f"check device {i} gpu mpmbop info {mode} {dict_key['name']} is fail ")

    def check_gpu_smi_ecc(self):
        cmd = "ppu-smi -q -d ECC"
        output = self.execute_run(cmd).data
        output_list = re.findall('SRAM.*', output, re.I)
        for output in output_list:
            check_info = output.split()[-1]
            if check_info !=  "N/A":
                self.logger.error(f"check  gpu smi ECC info is fail ")
                raise Exception(f"check  gpu smi ECC info is fail ")
        output_list = re.findall('DRAM.*', output, re.I)
        for output in output_list:
            check_info = output.split()[-1]
            if check_info !=  "0":
                self.logger.error(f"check  gpu smi ECC info is fail ")
                raise Exception(f"check  gpu smi ECC info is fail ")

    def check_ppu_hbm_degc(self, count):
        for i in range(count):
            cmd = f"ppudbg --device {i} --time 1 --monitor power"
            output = self.execute_run(cmd).data
            filter_info = output.split('\n')[1]
            ppu_degc = int(filter_info.split()[8])
            if ppu_degc >60 or ppu_degc <20 :
                self.logger.error(f"check  gpu device {i} ppu degC info is fail ")
                raise Exception(f"check  gpu device {i} ppu degC info is fail ")
            self.logger.info(f'ppu_degc : {ppu_degc} check pass')
            hib_degc_list = filter_info.split()[9].split('/')
            for degc in hib_degc_list:
                degc = int(degc)
                if degc >60 or degc <20 :
                    self.logger.error(f"check  gpu device {i} hib degC info is fail ")
                    raise Exception(f"check  gpu device {i} hib degC info is fail ")
                self.logger.info(f'ppu_degc : {hib_degc_list} check pass')

    def check_times(self):
        for i in range(8):
            cmd = f"ppudbg --read 0x5fdfc --device {i}"
            output = self.execute_run(cmd).data
            time1 = int(output, 16) / 1000000
            cmd = f"ppudbg --read 0x5fdfd --device {i}"
            output = self.execute_run(cmd).data
            time2 = int(output, 16) / 1000000
            diff = time2 - time1
            if diff >= 1:
                self.logger.info(f"device {i} 时间差为{diff:.2f}s: 大于1s")
            else:
                self.logger.info(f"device {i} 时间差为{diff:.2f}s: 小于1s")
                raise Exception(f"device {i} 时间差为{diff:.2f}s: 小于1s")

    def check_gpu_device(self, count):
        for i in range(count):
            cmd = f"ppudbg --device {i}"
            output = self.execute_run(cmd).data
            info = re.findall('HBM Frequency.*', output , re.I)[0]
            if info.count("1800MHZ") != 3:
                self.logger.error(f"check gpu device HBM {i} Frequency is fail ")
                raise Exception(f"check gpu device HBM {i} Frequency is fail ")
            
    def get_gpu_counts(self):
        cmd = "ppudbg --list"
        output = self.execute_run(cmd).data
        output = output.splitlines()
        gpu_count = 0
        for line in output:
            if "DID:" in line:
                gpu_count += 1
        if gpu_count == 8 :
            self.logger.info("check gpu count is pass ")
        else:
            self.logger.error("check gpu count is fail ")
            raise Exception("")
        self.logger.info(f"gpu count is {gpu_count}")
        return gpu_count

    def oam_check(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            ppu_count = self.get_gpu_counts()
            self.check_gpu_device(ppu_count)
            self.check_gpu_monitor(ppu_count)
            self.check_gpu_lspci(ppu_count)
            self.check_gpu_icn(ppu_count)
            self.check_gpu_micnop_prbs(ppu_count)
            self.check_gpu_micnop_stat(ppu_count)
            self.check_gpu_mpmbop_info(ppu_count, 0)
            self.check_gpu_mpmbop_info(ppu_count, 1)
            self.check_gpu_smi_ecc()
            self.check_ppu_hbm_degc(ppu_count)

    def check_times(self):
        with self.ssh_connect(uut=self.config["UUT"]):
            for i in range(8):
                cmd = f"ppudbg --read 0x5fdfc --device {i}"
                output = self.execute_run(cmd).data
                time1 = int(output, 16) / 1000000
                cmd = f"ppudbg --read 0x5fdfd --device {i}"
                output = self.execute_run(cmd).data
                time2 = int(output, 16) / 1000000
                diff = time2 - time1
                if diff >= 1:
                    self.logger.info(f"device {i} 时间差为{diff:.2f}s: 大于1s")
                else:
                    self.logger.info(f"device {i} 时间差为{diff:.2f}s: 小于1s")
                    raise Exception(f"device {i} 时间差为{diff:.2f}s: 小于1s")

    def check_receiver_rx(self, x_fist_list, y_fist_list, inittype=True):
        with self.ssh_connect(uut=self.config["UUT"]):
            if inittype:
                parser = self.execute_run("ppudbg --event clear")
            for i in range(8):
                parser = self.execute_run(f'ppudbg --event dump --device {i} |grep -i "Receiver Error" | head -n 1').data
                x1 = re.search(' Error counter is : (\d+)', parser ).group(1)
                if inittype:
                    x_fist_list.append(x1)
                else:
                    self.logger.info(f"device {i} Receiver Error old count :{x_fist_list[i]}, now : {x1} ")
                    if (int(x1) - int(x_fist_list[i]) ) > 10:
                        self.fail(f'device {i} Receiver Error gt 10')
                parser = self.execute_run(f'ppudbg --event dump --device {i} |grep -i "Rx Recovery" |head -n 1').data
                y1 = re.search('counter is : (\d+)', parser).group(1)
                if inittype:
                    y_fist_list.append(y1)
                else:
                    self.logger.info(f"device {i} Rx Recovery old count :{y_fist_list[i]}, now : {y1} ")
                    if (int(y1) - int(y_fist_list[i]) ) > 10:
                        self.fail(f'device {i} Rx Recovery gt 10')
            return x_fist_list, y_fist_list
        
    def health_check(self):
        http_server_url = self.mes_info["info"]["http_server_url"]
        _kk = os.path.join(http_server_url, "LuxScript/tools/ancoan/kingkong/")
        kkpath = self.config["kkpath"]
        kingkong_path_zip = kkpath["kingkong"]
        kingkong_zip = os.path.split(kingkong_path_zip)[-1]
        kingkong_name = kingkong_zip[:-4]
        _path = os.path.dirname(self.root_path)
        kingkong_dir = os.path.join("/root", kingkong_name)
        self.os_run.run(f"cd {_path};wget -t 5 -T 60 -r -np -nH -R index.html {_kk}")
        with self.ssh_connect(uut=self.config["UUT"]):
            self.execute_run(f"rm -rf {kingkong_dir}")
            self.execute_run(f"unzip {kingkong_path_zip}")
            cmd = f"python {kingkong_dir}/kk.pyc -t default -m default -c {kingkong_dir}/testcase/testcase_healthcheck.yaml -d default"
            parser = self.execute_run(cmd)
            ret = parser.get_value(f"Final_Result: (PASS)")
            self.assertEqual(ErrorCode.FFFFFFFF, "health check Final_Result ", ret.lower(), "pass")


    def clear_sel_log(self):
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            parser = self.execute_run("ipmitool sel list")
            parser = self.execute_run("ipmitool alioem sel list")
            for i in range(3):
                parser = self.execute_run("touch /logs/restorefactory")
                parser = self.execute_run("ipmitool sel clear")
                self.sleep(3)
            parser = self.execute_run("ipmitool raw 6 2", i_exit_code=True)
        with self.ssh_connect(uut=self.config["UUT"]):
            #清除机头bmc log 
            parser = self.execute_run("ipmitool sel list")
            parser = self.execute_run("ipmitool alioem sel list")
            self.execute_run(" ipmitool alioem restoretomanufacturesetting ", i_exit_code=True)\
            
    def check_busid(self):
        work_path = os.path.dirname(self.root_path)
        _mes = MesSocket(self.mes_info["info"]["url"], self.mes_info["info"]["sn"])
        rk_num =  _mes.get_mes_info(self.mes_info["info"]["sn"])["Results"]["rk_part_number"]
        json_file = f"{work_path}/LuxScript/Luxshare-AncoanRT/100/Config/lspci_json_files/{rk_num}_lspci.json"
        lspci_tool = f'{work_path}/LuxScript/Luxshare-AncoanRT/100/create_lspci_dict.py'
        with self.ssh_connect(uut=self.config["UUT"]):
            cmd = f"cp {lspci_tool} /root "
            output = self.execute_run(cmd)
            cmd = f"python3 /root/create_lspci_dict.py"
            output = self.execute_run(cmd)
            cmd = f"diff /root/lspci.json {json_file}"
            output = self.execute_run(cmd, save_exit_code=True)
            if self.ssh.get_exit_code() != 0 :
                id_list = re.findall(r'\d+c\d+', output.get_origin_data())
                for bus_id in id_list:
                    _id = re.search(r"(\d+)c", bus_id).group(1)
                    cmd = f"cat /root/lspci.json |head -n {_id} |tail -n 5"
                    output = self.execute_run(cmd)
                raise Exception("check lspci is fail")

    def exe(self):
        receiver_list , rx_list = self.check_receiver_rx([], [])
        self.check_busid()
        self.health_check()
        self.oam_check()
        self.check_times()
        self.check_receiver_rx(receiver_list, rx_list, False)

if __name__ == '__main__':
    runner.single_runner(DcPowerCycleCheck)
