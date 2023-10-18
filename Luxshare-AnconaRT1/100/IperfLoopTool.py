'''
@Author  :   Zhao.Zhuang
@Contact :   Zhao.Zhuang@luxshare-ict.com
@Software:   TestCase
@Time    :   2022/04/24
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
'''



from argparse import ArgumentParser, RawTextHelpFormatter
import argparse
from ast import arg
import datetime
import imp
import logging
import multiprocessing
from operator import sub
import os
from re import I, L
import re
import time
import subprocess


from collections import namedtuple

reports_path = os.path.split(os.path.realpath(__file__))[0]
reports_path = reports_path + '/' + 'reports'
fio_log = f'{reports_path}/fio'
iperf_log = f'{reports_path}/iperf'
mem_log = f'{reports_path}/memtester'
cpu_log = f'{reports_path}/cpu'
dirlist=["fio" ,"iperf" ]
# dirlist=["fio" ,"iperf" ,"mem" ,"cpu" ]
process_list = []




def log():
    logger = logging.getLogger('reports')
    fh = logging.FileHandler(f'{reports_path}/reports.log')

    ch = logging.StreamHandler()

    fm = logging.Formatter('%(asctime)s :  %(message)s')

    fh.setFormatter(fm)

    ch.setFormatter(fm)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel("DEBUG")
    return logger


def os_cmd(command):
    """
    Execute OS system command
    :param command: system command can be executed in Linux Shell or Windows Command Prompt
    """
    print(command)

    if not isinstance(command, str):
        raise TypeError(f'command MUST be _cmd string type, {command} is _cmd {type(command)} type')
    SysCMD = namedtuple('SysCMD', ['returncode', 'output'])
    p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,shell=True)
    try:
        stdout = p.stdout.decode(encoding='ascii')
        stderr = p.stderr.decode(encoding='ascii')
    except :
        stdout = p.stdout.decode(encoding='utf8')
        stderr = p.stderr.decode(encoding='utf8')
    output = stdout + stderr
    return SysCMD(p.returncode, output)

def mkdir(dirs):
    #创建所有文件夹
    for dir in dirs:
        dir = reports_path + "/" + dir
        cmd = f"mkdir -p {dir}"
        rst = os_cmd(cmd)



def chcek_process():
    #检查进程是否全部开启
    status = True
    for key in process_list:
        count = os_cmd(f'ps -ef | grep -v grep | grep -c {key}').output
        for i in range(3):
            if key == 'iperf':
                if int(count) != len(nic_name) * 2:
                    time.sleep(5)
                    print(count)
                    if i == 2:
                        status = False
                    else:
                        continue
            if int(count) <= 1:
                logger.error(f'run {key} is fail')
                time.sleep(5)

                if i == 2:
                    status = False
                else:
                    continue

    if status:
        logger.info('run all process pass')
    else:
        raise Exception('run all process is fail')

def kill_process():
    # 关闭所有进程
    status = True
    for key in process_list:
        os_cmd(f'pkill -8 {key}')
        time.sleep(5)
        for i in range(3):
            count = os_cmd(f'ps -ef | grep -v grep | grep -c {key}').output
            if int(count) != 0:
                logger.error(f'kill {key} is fail')
                time.sleep(5)
                if i == 2:
                    status = False
            else:
                break
    if status:
        logger.info('kill all process pass')



def retry_cmd(cmd):
    #重复尝试命令
    for i in range(4):
        time.sleep(3)
        berfor_count = os_cmd(f'ps -ef | grep -v grep | grep -c iperf').output
        os.popen(cmd)
        time.sleep(3)
        after_count = os_cmd(f'ps -ef | grep -v grep | grep -c iperf').output
        if int(after_count) == int(berfor_count) + 1:
            return         


def loop_iperf(dict):
    #开启loop iperf
    _nic_name_list = dict['nic_name']
    port = 6030
    for _nic_names in _nic_name_list:
        cmd = f"nohup iperf -B {nic_dict[_nic_names[1]]['ip']} -s -p {port} 2>&1 &"
        logger.info(cmd)
        retry_cmd(cmd)
        cmd = f"nohup iperf -B {nic_dict[_nic_names[0]]['ip']} -c {nic_dict[_nic_names[1]]['ip_client']}  -t {runtime} -i 5 -p {port} -P 4 >> {iperf_log}/iperf_{_nic_names[0]}_client.log 2>&1 &"
        logger.info(cmd)
        retry_cmd(cmd)
        port += 1

def check_iperf_loop_test(dict):
    logger.info('check iperf test is run')
    _nic_name_list = dict['nic_name']
    port = 4030
    for _nic_names in _nic_name_list:
        cmd = f"nohup iperf -B {nic_dict[_nic_names[1]]['ip']} -s -p {port}  2>&1 &"
        logger.info(cmd)
        os.popen(cmd)
        cmd = f"iperf -B {nic_dict[_nic_names[0]]['ip']} -c {nic_dict[_nic_names[1]]['ip_client']}  -t 5 -i 2 -p {port} -P 4 "
        logger.info(cmd)
        rst = os_cmd(cmd).output.strip()
        if 'connected' not in rst:
            raise Exception(f'{_nic_names} iperf fail')
        port += 1
    os.popen('pkill -8 iperf')

def nic_mac(ports):
    # 获取网卡的mac地址
    for port in ports:
        for name in port:
            cmd = "ifconfig %s |grep ether |awk '{print $2}'" % name
            rst = os_cmd(cmd).output.strip()
            nic_dict[name] ={'mac':rst}

def get_nic_name():
        nic_name_list = []
        cmd = "lspci |grep -i eth |awk '{print $1}'"
        bus_id_list = os_cmd(cmd).output.strip().split('\n')
        for i in range(0, len(bus_id_list), 2):
            cmd = f"ls /sys/bus/pci/devices/{bus_id_list[i]}/net"
            nic_name_1 = os_cmd(cmd).output.strip()
            cmd = f"ls /sys/bus/pci/devices/{bus_id_list[i+1]}/net"
            nic_name_2 = os_cmd(cmd).output.strip()
            nic_name_list.append([nic_name_1,nic_name_2])
        print(nic_name_list)
        return nic_name_list

def set_loop_route(nic_names_list):
    #回环静态路由
    cmd ='iptables -t nat -F'
    os_cmd(cmd)
    time.sleep(30)
    logger.info('clear nat list')
    num_1 = 100
    for _nic_names in nic_names_list:
        ip_0 = f'192.168.{num_1}.1'
        ip_1 = f'192.168.{num_1+1}.1'
        ip_2 = f'192.168.{num_1+2}.1'
        ip_3 = f'192.168.{num_1+3}.1'
        nic_dict[_nic_names[0]]['ip'] = ip_0
        nic_dict[_nic_names[0]]['ip_client'] = ip_2
        nic_dict[_nic_names[1]]['ip'] = ip_1
        nic_dict[_nic_names[1]]['ip_client'] = ip_3

        #set ip
        cmd = f'ifconfig {_nic_names[0]} 100.100.100.1/24'
        os_cmd(cmd)
        cmd = f'ifconfig {_nic_names[0]} {ip_0}/24'
        os_cmd(cmd)
        cmd = f'ifconfig {_nic_names[1]} 100.100.100.2/24'
        os_cmd(cmd)
        cmd = f'ifconfig {_nic_names[1]} {ip_1}/24'
        os_cmd(cmd)
        cmd = f'iptables -t nat -A POSTROUTING -s {ip_0} -d {ip_3} -j SNAT  --to-source {ip_2}'
        os_cmd(cmd)
        cmd = f'iptables -t nat -A PREROUTING -d {ip_2} -j DNAT --to-destination {ip_0}'
        os_cmd(cmd)
        cmd = f'iptables -t nat -A POSTROUTING -s {ip_1} -d {ip_2} -j SNAT  --to-source {ip_3}'
        os_cmd(cmd)
        cmd = f'iptables -t nat -A PREROUTING -d {ip_3} -j DNAT --to-destination {ip_1}'
        os_cmd(cmd)
        cmd = f'ip route add {ip_3} dev {_nic_names[0]}'
        os_cmd(cmd)
        cmd = f'ip route add {ip_2} dev {_nic_names[1]}'
        os_cmd(cmd)

        cmd = f'arp -i {_nic_names[0]}  -s {ip_3} {nic_dict[_nic_names[1]]["mac"]}'
        os_cmd(cmd)
        cmd = f'arp -i {_nic_names[1]}  -s {ip_2} {nic_dict[_nic_names[0]]["mac"]}'
        os_cmd(cmd)
        num_1 += 10


class Process(object):

    def __init__(self, dev_list) -> None:
        self.pool = multiprocessing.Pool(len(dev_list)+15)

    def run_process(self, funcname, *args, **kwargs):

        self.pool.apply_async(func=funcname,args=(kwargs, ) )

if __name__== '__main__':
    parser = ArgumentParser(
        description='machine pressure test',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument('-rt', '--runtime',
                        type=int, default=43200,
                        help="sprict is run time second")

    parser.add_argument('-st', '--sleeptime',
                    type=int, default=0,
                    help="sprict is idle time second")



    iperf_port= [10,11]

    args = parser.parse_args()
    runtime = args.runtime
    sleeptime = args.sleeptime
    nic_dict ={}
    nic_name = get_nic_name()


    nic_list = os_cmd( "ls /sys/class/net/ | grep -Ev 'docker|lo|virbr'").output.strip().split()
    for nic in nic_name:
        if nic[0] not in nic_list:
            raise Exception(f'not found nic port name : {nic[0]}')
        if nic[1] not in nic_list:
            raise Exception(f'not found nic port name : {nic[0]}')
    print('check nic port is pass')



    if os.path.exists(reports_path):
        print(f'remove {reports_path}')
        os_cmd(f" rm -rf {reports_path}")

    mkdir(dirlist)
    logger = log()
    start_time = time.perf_counter()
    logger.info('======Script start ========')


    nic_mac(nic_name)
    set_loop_route(nic_name)
    dict1 = {'nic_name': nic_name}
        # loop_iperf(dict1)
    check_iperf_loop_test(dict1)


    drives_list = [0,0,0,0]
    os_cmd(f"sar -n DEV 1 >> {iperf_log}/sar.log 2>&1 &")
    while runtime > 0:
        #创建进程池
        start_time = time.perf_counter()
        p = Process(drives_list)

    
        dict1 = {'nic_name': nic_name}
        # loop_iperf(dict1)
        logger.info('iperf loop test is running ')
        if 'iperf' not in process_list:
            process_list.append('iperf')
        #p.run_process(funcname=loop_iperf, nic_name=nic_name)

            loop_iperf(dict1)
        p.pool.close()
        cycletime = time.perf_counter()
        time.sleep(5)
        chcek_process()


        if sleeptime !=0:
            logger.info('Dynamic Load Testing')
            time.sleep(sleeptime)
            end_time = time.perf_counter()

        else:
            logger.info('Machine load test')
            while runtime>0:
                start_time = time.perf_counter()
                time.sleep(60)
                end_time = time.perf_counter()
                logger.info(f'run: {(end_time - start_time)}')
                runtime = runtime - (end_time - start_time)
                print(f'runtime : {runtime}')

        p.pool.terminate()
        kill_process()
        if sleeptime !=0:
            time.sleep(sleeptime)
        p.pool.join()
        logger.info(f'run: {(end_time - start_time)}')
        runtime = runtime - (end_time - start_time)
        print(f'runtime : {runtime}')
    logger.info('======Script end ========')
    os_cmd("pkill -9 iperf")
    os_cmd("pkill -9 sar")
