# coding: utf-8
# author: Sun
# date: 2024/10/31
import queue
import threading
import traceback
from logging import exception

import serial
import serial.tools.list_ports
import logging
import time
import re
import paramiko
import sys
import socket
from multiprocessing import Process, Queue

IP = "192.168.10.62"
USERNAME = "root"
PASSWORD = "1"
# 功耗获取命令
POWERCOMMAND = "power_read"
# 温度获取命令
TEMPCOMMAND = "pvt getcali 0 0 0"
# 电压获取命令
VDDCOMMAND = "pvt getall"
# 筛片shell脚本名称,建议脚本放置/root目录下
SCRIPTNAME = "slt_dpdu_of_nopower_x4_1.sh"
SERIALPORT = "COM4"
BAUDRATE = 230400
LOGFILE = "log_%s.log" % time.strftime("%Y%m%d%H%M%S", time.localtime())
# 设置日志打印格式
# 创建logger
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)  # 设置日志级别
# 创建控制台处理器
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# 创建file handler
fh = logging.FileHandler(LOGFILE)
fh.setLevel(logging.INFO)
# 创建格式器并绑定到处理器
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)s - %(message)s')
# ch.setFormatter(formatter)
# fh.setFormatter(formatter)
# 将处理器添加到logger
logger.addHandler(ch)
logger.addHandler(fh)


def serread(address, serialport=SERIALPORT):
    ser = serial.Serial(serialport, BAUDRATE, timeout=10, write_timeout=5)
    ser.write(b"\r\n")
    ser.write(b"regr %s\r\n" % str(address).encode("utf-8"))
    time.sleep(1)
    retcontent = ser.read_all()
    ser.close()
    parsevalue = re.search(b"value = ([0-9a-f]+)", retcontent)
    return parsevalue.group(1)


def sersend(cmd, serialport=SERIALPORT):
    ser = serial.Serial(serialport, BAUDRATE, timeout=10, write_timeout=5)
    ser.write(b"\r")
    ser.write(f"{cmd}\r".encode("utf-8"))
    time.sleep(1)
    retcontent = ser.read_all()
    ret = retcontent.decode("utf-8")
    ser.close()
    # print(retcontent.decode())
    retcontentlist = retcontent.decode().split("\r\n")
    for i in range(len(retcontentlist)):
        if retcontentlist[i].strip() == "" or retcontentlist[i].strip() == "cmd>":
            continue
        logger.info(str(retcontentlist[i]))
    return ret


def portcheck(serialport=SERIALPORT):
    ser = serial.Serial(serialport, BAUDRATE, timeout=10, write_timeout=5)
    ser.write(b"\r\n")
    flag = True
    num = 0
    for m in range(7):
        for n in [1, 2, 3, 4]:
            ser.write(b"lt_his %s %s\r\n" % (str(m).encode(), str(n).encode()))
            time.sleep(0.5)
            retcontent = ser.read_all()
            retcontentlist = retcontent.decode().split("\r\n")
            for i in range(len(retcontentlist)):
                if "Cur link Status Cap:" in retcontentlist[i]:
                    num += 1
                    # if m == 2 and n == 1:
                    if "GEN5 X16" not in retcontentlist[i]:
                        res = retcontentlist[i].split("-")[-1]
                        logger.error("S{}P{}降为{}".format(m, n, res))
                        flag = False
                    else:
                        logger.info(f"S{m}P{n}" + str(retcontentlist[i]))
                    # else:
                    #     if "GEN5 X4" not in retcontentlist[i]:
                    #         res = retcontentlist[i].split("-")[-1]
                    #         logger.error("S{}P{}降为{}".format(m, n, res))
                    #         flag = False
                    #     else:
                    #         logger.info(f"S{m}P{n}" + str(retcontentlist[i]))
    if not flag:
        raise Exception("存在降速降lane，建链检查失败！！！")
    if num != 6:
        raise Exception("建链数据不足，建链检查失败！！！")


# ser.write(b"lt_his %s %s\r\n" % (str(6).encode(), str(2).encode()))
# time.sleep(0.5)
# retcontent = ser.read_all()
# retcontentlist = retcontent.decode().split("\r\n")
# for i in range(len(retcontentlist)):
#     if "Cur link Status Cap:" in retcontentlist[i]:
#         logger.info(f"S6P2" + str(retcontentlist[i]))


def remotecmd(cmd, ip=IP, username=USERNAME, password=PASSWORD, port=22):
    """
    :param port:
    :param cmd: remote command or script
    :param ip: remote server ip
    :param username: remote server os username
    :param password: remote server os password
    :return:
    """
    status = False
    # 创建SSH客户端
    client = paramiko.SSHClient()
    # 自动添加未知的服务器密钥及策略
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # 连接SSH服务端
        client.connect(hostname=ip, port=port, username=username, password=password, timeout=30)
        # 执行命令
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=False)
        # 实时读取输出
        while True:
            # 读取标准输出
            if stdout.channel.recv_ready():
                sys.stdout.write(stdout.channel.recv(1024).decode('utf-8', errors='ignore'))
                sys.stdout.flush()
            # 读取标准错误
            if stdout.channel.recv_stderr_ready():
                sys.stderr.write(stdout.channel.recv_stderr(1024).decode('utf-8', errors='ignore'))
                sys.stderr.flush()
            # 检查命令是否结束
            if stdout.channel.exit_status_ready():
                break
        status = stdout.channel.recv_exit_status()
        if status:
            logger.error(f"remote command:{cmd} exec failed, return code is {status}")
        else:
            logger.info(f"remote command:{cmd} exec success")
    except paramiko.AuthenticationException:
        logger.error("认证失败！")
        return None
    except paramiko.SSHException as e:
        logger.error(f"SSH连接错误: {e}")
        return None
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        logger.error(f"连接{ip}失败...")
        return None
    except socket.timeout:
        logger.error(f"连接超时：无法在10秒内连接到 {ip}")
        return None
    finally:
        # 关闭连接
        client.close()
    return status


def getcmdserialport():
    global SERIALPORT
    portlist = list(serial.tools.list_ports.comports())
    portnamelist = [ser.device for ser in portlist]
    if not portnamelist:
        logger.error("Cannot find serial port")
        exit(1)
    else:
        logger.info("Found serial port " + str(portnamelist))
    for serport in portnamelist:
        try:
            ser = serial.Serial(serport, BAUDRATE, timeout=10, write_timeout=5)
            ser.write(b"c\r\n")
            time.sleep(1)
            retdata = ser.read_all()
            if b'password' in retdata:
                ser.write(b"sudo@2025\r\n")
            if retdata == b'':
                continue
        except serial.SerialException:
            logger.info(f"Serial port: {serport} is busy...")
            continue
        else:
            ser.write(b"\r\n")
            time.sleep(1)
            retdata = ser.read_all()
            if b'cmd>' in retdata:
                logger.info(f"{serport} is command serial port")
                SERIALPORT = serport
                break
            ser.close()
    if not SERIALPORT:
        logger.error("Cannot find command serial port")
        exit(1)


def fiotest(q, ip, username, password, serialport):
    try:
        logger.info("------fio测试前功耗读取------")
        sersend(f"{POWERCOMMAND}", serialport)
        sersend(f"{TEMPCOMMAND}", serialport)
        sersend(f"{VDDCOMMAND}", serialport)
        ret = remotecmd(f"cd /home/sd/hyp; bash ./{SCRIPTNAME}", ip, username, password)
        logger.info("+++++fio测试后功耗读取+++++")
        sersend(f"{POWERCOMMAND}", serialport)
        sersend(f"{TEMPCOMMAND}", serialport)
        sersend(f"{VDDCOMMAND}", serialport)
        if ret != 0:
            q.put(-1)
        else:
            q.put(ret)

    except Exception as e:
        logger.error(f"未知错误: {e}")
        q.put(-1)


def test_fiostress(ip=IP, username=USERNAME, password=PASSWORD):
    """
    测试fio
    """
    processes = []
    q = Queue()
    # time.sleep(120)
    processes += [
        Process(target=fiotest, args=(q, ip, username, password, SERIALPORT))
    ]

    for p in processes:
        p.start()

    for p in processes:
        p.join(5)

    process_copy = processes[:]
    return_sum = 0
    while True:
        for p in process_copy:
            if p.is_alive():
                p.join(timeout=50)
                logger.info("*******fio测试中功耗读取*******")
                sersend(f"{POWERCOMMAND}", serialport=SERIALPORT)
                sersend(f"{TEMPCOMMAND}", serialport=SERIALPORT)
                sersend(f"{VDDCOMMAND}", serialport=SERIALPORT)
            else:
                return_sum += q.get()
                process_copy.remove(p)
                if return_sum != 0:
                    for p1 in process_copy:
                        p1.terminate()
                    break
        else:
            if len(process_copy) == 0 or return_sum != 0:
                break
            time.sleep(50)

    assert return_sum == 0, "fio stress测试---------------------------------------------[失败]"
    logger.info("fio stress测试---------------------------------------------[成功]")

def get_aer_info():
    logger.info("===============Start autotesting...==================")
    getcmdserialport()
    logger.info("获取串口AER信息")
    sersend("aer all", SERIALPORT)

def check_link_is_l1():
    logger.info("===============Start autotesting...==================")
    getcmdserialport()
    logger.info("获取串口链路状态信息")
    res = sersend("lt_his all", SERIALPORT)
    port_list = re.findall(r"([\d|a-zA-Z]+)\s-", res)
    print(port_list)
    for port in port_list:
        if port[1] != "2":
            res = sersend(f"lt_his {port[1]} {port[3]}", SERIALPORT)
            assert "L1" in res.split("\r\n")[3], f"{port}建链状态异常"

def check_have_equalization():
    logger.info("===============Start autotesting...==================")
    getcmdserialport()
    logger.info("获取串口链路状态信息")
    res = sersend("lt_his all", SERIALPORT)
    port_list = re.findall(r"([\d|a-zA-Z]+)\s-", res)
    print(port_list)
    for port in port_list:
        if port[1] != "2":
            res = sersend(f"lt_his {port[1]} {port[3]}", SERIALPORT)
            assert "Recovery.Equalization3" in res.split("\r\n")[7], f"{port}未发生过均衡"

# def monitor(q):
#     while True:
#         if not q.empty():
#             break
#         with r:
#             try:
#                 sersend("dfs get", SERIALPORT)
#                 sersend(f"{TEMPCOMMAND}", SERIALPORT)
#                 sersend(f"{POWERCOMMAND}", SERIALPORT)
#                 # sersend(f"{VDDCOMMAND}", SERIALPORT)
#             except Exception as e:
#                 q.put(e)
#                 logger.error("{}".format(traceback.format_exc()))
#         time.sleep(1)
#
#
# def link_check(q):
#     while True:
#         if not q.empty():
#             break
#         with r:
#             try:
#                 logger.info("====================fio压测之前,建链检查===================")
#                 portcheck(serialport=SERIALPORT)
#             except Exception as e:
#                 q.put(e)
#                 logger.error("{}".format(traceback.format_exc()))
#         time.sleep(90)


####main####
if __name__ == '__main__':
    if sys.argv[1] == "aer":
        get_aer_info()
    elif sys.argv[1] == "check_l1":
        check_link_is_l1()
    elif sys.argv[1] == "check_eq":
        check_have_equalization()
