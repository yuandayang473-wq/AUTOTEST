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

from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Constant import ErrorCode
from Utils.Init import load_mes_info
from Lib.Request import MesSocket
from Utils.Login import ApcConnect
from test_case.BaseConfigCheck import BaseConfigCheck


class PowerCycle(BaseConfigCheck):
    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "PowerCycle"
        self.expect = "This is PowerCycle for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key":"UUT_01"},
            {"file": "PduDevice.yaml", "name": "pdu", "key": self.locals["PDU"]},{"file": "BmcDevice.yaml", "name": "JBMC", "key":"BMC_02"},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": "BMC_02"},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "path", "key": "InitPath"},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "oam_conf", "key": "OAM"},
            {"folder": "Luxshare-AnconaPT/100/Config", "file": "UUT.yaml", "name": "lspcipath", "key": "Lspci"},
            {"file": "BmcDevice.yaml", "name": "BMC_HEADER", "key": "BMC_03"},
        ]
        
    def health_check(self):
        path = self.config["path"]
        kingkong_path_zip = os.path.join(path["test_path"], path["kingkong"])
        kingkong_dir = os.path.join("/root", path['kingkong_dir'])
        self.execute_run(f"rm -rf {kingkong_dir}")
        self.execute_run(f"unzip {kingkong_path_zip}")
        # cmd = "python kk.pyc -t default -m default -c ./testcase/testcase_healthcheck.yaml -d default"
        cmd = f"python {kingkong_dir}/kk.pyc -t default -m default -c {kingkong_dir}/testcase/testcase_healthcheck.yaml -d default"
        parser = self.execute_run(cmd, i_exit_code=True)

        ret = parser.get_value(f"Final_Result: (PASS)")
        self.assertEqual(ErrorCode.FFFFFFFF, "health check Final_Result ", ret.lower(), "pass")

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

                    
    def config_check(self):
        self.cpu()
        self.memory()
        self.nvme()
        self.ssd()
        self.gpu()
        self.head_psu()
        back_ssh = self.ssh
        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            self.tail_psu()
        self.ssh = back_ssh
            

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

    def oam_chcek(self):
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

    def fopen(self, file='', content='', mode='r', json=False, path=None):
        '''
        description: read or write file
        author: zhuang zhao
        params: file, the file want to operate.
                content, the msg that want to be written to file.
                mode, the open file mode, choose from [r, w, a]
                json, use when deal json date, choices:[True, False]
        return: data, the file's reading date
        '''
        # transfer dat file to dat_dict
        now = time.strftime("%a %b %d %H:%M:%S %Y",time.localtime())
        data = ''
        f = open(file, mode, encoding='UTF-8')
        if mode == 'w' or mode == 'a':
            if json:
                f.write(dumps(content, indent=4, sort_keys=False) + '\n')
            else:
                f.write(now + " : " + content + "\n")
        else:
            if json:
                data = eval(f.read())
            else:
                data = f.read()
        f.close()
        return data

    def ping_pang(self, ip, sleep_time=5, mode="off"):
        for i in range(20):
            output = os.popen(f'ping {ip} -w 5 ').read()
            self.logger.info(f"ping {ip} -w 5 ")
            self.logger.info(f"{output}")
            if mode == "off":
                if " 100% packet loss" in output or "请求超时" in output :
                    self.logger.info("set pdu is pass ")
                    break
            elif i == 19:
                self.logger.error(f"set pdu is fail ") 
                raise Exception("set pdu is fail ")
            else:
                if " 100% packet loss" not in output and "请求超时" not in output :
                    self.logger.info("set pdu is pass ")
                    break
            self.sleep(sleep_time)

    def check_busid(self):
        _file = self.config["lspcipath"]["file"]
        _tool = self.config["lspcipath"]["tool"]

        # dict_list = {}
        # lspci_info = self.fopen(file=_file, mode='r', json=True)
        # cmd = " lspci"
        # output = self.execute_run(cmd).data.strip().split('\n')
        # for info in output:
        #     dict_info = {}
        #     id = info.split(" ")[0]
        #     cmd = f"lspci -s {id} -vvv  "
        #     pci_info = self.execute_run(cmd).data
        #     output = re.findall(f"{id}.*", pci_info, re.I)[0]
        #     name = output.split(': ')[0]
        #     self.logger.info(f'check lspci busid : {id}, name : {lspci_info[id]["name"]} {name}')
        #     if lspci_info[id]["name"] != name:
        #         raise Exception(f'check lspci busid : {id}, name : {lspci_info[id]["name"]} =! {name}')

        #     lnkcap = re.findall(f"LnkCap:.*", pci_info, re.I)
        #     if lnkcap:
        #         lnkcap = lnkcap[0].split(":\t")[1].strip()
        #         self.logger.info(f'check lspci busid : {id}, lnkcap : {lspci_info[id]["lnkcap"]} {lnkcap}')
        #         if lspci_info[id]["lnkcap"].strip() != lnkcap:
        #             raise Exception(f'check lspci busid : {id}, lnkcap : {lspci_info[id]["lnkcap"]} =! {lnkcap}')

        #     lnksta = re.findall(f"LnkSta:.*", pci_info, re.I)
        #     if lnksta:
        #         lnksta= lnksta[0].split(":\t")[1].strip()
        #         self.logger.info(f'check lspci busid : {id}, lnksta : {lspci_info[id]["lnksta"]} {lnksta}')
        #         if lspci_info[id]["lnksta"].strip() != lnksta:
        #             raise Exception(f'check lspci busid : {id}, lnksta : {lspci_info[id]["lnksta"]} =! {lnksta}')

        #     uesta = re.findall(f"UESta:.*", pci_info, re.I)
        #     if uesta:
        #         uesta = uesta[0].split(":\t")[1].strip()
        #         self.logger.info(f'check lspci busid : {id}, uesta : {lspci_info[id]["uesta"]} {uesta}')
        #         if lspci_info[id]["uesta"].strip() != uesta:
        #             raise Exception(f'check lspci busid : {id}, uesta : {lspci_info[id]["uesta"]} =! {uesta}')

        #     cesta = re.findall(f"CESta:.*", pci_info, re.I)
        #     if cesta:
        #         cesta = cesta[0].split(":\t")[1].strip()
        #         self.logger.info(f'check lspci busid : {id}, cesta : {lspci_info[id]["cesta"]} {cesta}')
        #         if lspci_info[id]["cesta"].strip() != cesta:
        #             raise Exception(f'check lspci busid : {id}, cesta : {lspci_info[id]["cesta"]} =! {cesta}')
        _mes = MesSocket(self.mes_info["info"]["url"],self.mes_info["info"]["sn"])
        rk_num = _mes.get_mes_info(self.mes_info["info"]["sn"])["Results"]["rk_part_number"]
        cmd = f"cp {_tool} /root "
        output = self.execute_run(cmd)
        cmd = f"python3 /root/create_lspci_dict.py"
        output = self.execute_run(cmd)
        cmd = f"diff /root/lspci.json {_file}{rk_num}_lspci.json"
        output = self.execute_run(cmd)

    
    def inittool(self):
        path = self.config["InitPath"]
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
        self.execute_run(f"cp -rf {path.get('mount_path')}{path.get('aliaom_driver')} {path.get('test_path')}")
        self.execute_run(f"cp -rf {path['fw_source_path']} {path.get('fw_path')}")
        self.execute_run(f"cp -rf {path['mount_path']}kingkong/{path['kingkong']} {path.get('test_path')}")
        self.execute_run(f"cp -rf /mnt/fru/* {path.get('fru_path')}")
        self.execute_run(f"rpm -ivh --nodeps --force {path.get('test_path')}{path.get('aliaom_driver')}")
        self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}mft-4.20.1-14.x86_64.rpm")
        self.execute_run(f"rpm -ivh --nodeps --force {path.get('mount_path')}sshpass-1.09-4.el8.x86_64.rpm")
        self.execute_run("chmod -R 777 /opt/Alioam/")

        # self.execute_run(f'{path["oampower_read_script"]}')
        
    
    def power_cycle_ac(self):
        # ac 操作
        user = {
            "ip_address": "localhost",
            "password": "1",
            "username": "root"
        }
        pdu = self.config["pdu"]
        head_pdu_con = ApcConnect(ip=pdu["ip_address"], pdu_mode=pdu["pdu_model"], port=pdu["head_port"])
        tail_pdu_con = ApcConnect(ip=pdu["ip_address"], pdu_mode=pdu["pdu_model"], port=pdu["tail_port"])
        with self.ssh_connect(uut=user):
            self.logger.info("server power off")
            head_pdu_con.pdu_off(self)
            self.ping_pang(self.os_ip)
            self.logger.info("jbog power off")
            tail_pdu_con.pdu_off(self)
            self.ping_pang(self.jbmc_ip)
            self.logger.info("jbog power on")
            tail_pdu_con.pdu_on(self)
            self.ping_pang(self.jbmc_ip, sleep_time=10, mode="on")
            self.logger.info("server power on")
            head_pdu_con.pdu_on(self)
            self.ping_pang(self.os_ip, sleep_time=60, mode="on")

    def power_cycle_dc(self):
        # ac 操作
        user = {
            "ip_address": "localhost",
            "password": "1",
            "username": "root"
        }
        tail_bmc_ip = self.config["JBOG_BMC"]["ip_address"]
        header_bmc_ip = self.config["BMC_HEADER"]["ip_address"]
        with self.ssh_connect(uut=user):
            self.logger.info("server dc cycle off")
            self.execute_run(f"ipmitool -I lanplus -H {header_bmc_ip} -U taobao -P 9ijn0okm power off" )
            self.logger.info("jbog dc cycle ")
            self.execute_run(f"ipmitool -I lanplus -H {tail_bmc_ip} -U admin -P admin chassis power cycle" )
            self.sleep(120)
            self.execute_run(f"ipmitool -I lanplus -H {header_bmc_ip} -U taobao -P 9ijn0okm power on" )
            self.logger.info("server dc cycle on ")
            self.ping_pang(self.os_ip, sleep_time=60, mode="on")


if __name__ == '__main__':
    runner.single_runner(PowerCycle)

