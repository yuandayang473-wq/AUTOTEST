# coding: utf-8
# author: Sun
# date: 2024/10/31
import queue
import threading
import traceback
import _thread
from logging import exception
from time import sleep

import serial
import serial.tools.list_ports
import logging
import time
import re
import paramiko
import sys
import socket
from multiprocessing import Process, Queue

IP = "192.168.10.217"
USERNAME = "root"
PASSWORD = "1"
# 功耗获取命令
POWERCOMMAND = "power_read"
# 温度获取命令
TEMPCOMMAND = "pvt getcali 0 0 1"
# PVT获取命令
PVTCOMMAND = "pvt getall"
# 筛片shell脚本名称,建议脚本放置/root目录下
SCRIPTNAME = "slt_dpdu_of_nopower_x4_1.sh"
SERIALPORT = ""
BAUDRATE = 230400
LOGFILE = "log_%s.log" % time.strftime("%Y%m%d%H%M%S", time.localtime())
# 设置日志打印格式
# 创建logger
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)  # 设置日志级别
# 创建控制台处理器
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# 创建file handler
fh = logging.FileHandler(LOGFILE)
fh.setLevel(logging.DEBUG)
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


def sersend(cmd, serialport=SERIALPORT, log_response=True):
    ser = serial.Serial(serialport, BAUDRATE, timeout=10, write_timeout=5)
    ser.write(b"\r")
    ser.write(f"{cmd}\r".encode("utf-8"))
    time.sleep(0.1)
    retcontent = ser.read_all()
    ret = retcontent.decode("utf-8")
    ser.close()
    # print(retcontent.decode())
    retcontentlist = retcontent.decode().split("\r\n")
    if log_response:
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
    for m in range(9):
        for n in [1]:
            ser.write(b"lt_his %s %s\r\n" % (str(m).encode(), str(n).encode()))
            time.sleep(0.5)
            retcontent = ser.read_all()
            retcontentlist = retcontent.decode().split("\r\n")
            for i in range(len(retcontentlist)):
                if "Cur link Status Cap:" in retcontentlist[i]:
                    num += 1
                    if m == 3 and n == 1:
                        if "GEN5 X16" not in retcontentlist[i]:
                            res = retcontentlist[i].split("-")[-1]
                            logger.error("S{}P{}降为{}".format(m, n, res))
                            flag = False
                        else:
                            logger.debug(f"S{m}P{n}" + str(retcontentlist[i]))
                    elif m == 0 and n == 1 or m == 1 and n == 1 or m == 2 and n == 1 or m == 4 and n == 1 or m == 5 and n == 1 or m == 6 and n == 1 or m == 7 and n == 1 or m == 8 and n == 1:
                        if "GEN5 X16" not in retcontentlist[i]:
                            res = retcontentlist[i].split("-")[-1]
                            logger.error("S{}P{}降为{}".format(m, n, res))
                            flag = False
                        else:
                            logger.debug(f"S{m}P{n}" + str(retcontentlist[i]))
    if not flag:
        raise Exception("存在降速降lane，建链检查失败！！！")
    if num != 9:
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
    :param cmd: remote command or script
    :param ip: remote server ip
    :param username: remote server os username
    :param password: remote server os password
    :param port: remote server SSH port
    :return: a tuple of command return code and standard output
    """
    # 创建SSH客户端
    client = paramiko.SSHClient()
    # 自动添加未知的服务器密钥及策略
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # 连接SSH服务端
        client.connect(hostname=ip, port=port, username=username, password=password, timeout=30)
        # 执行命令
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=False)
        channel = stdout.channel
        output = []
        # 实时读取输出
        while not channel.exit_status_ready() or channel.recv_ready() or channel.recv_stderr_ready():
            # 读取标准输出
            if channel.recv_ready():
                chunk = channel.recv(1024).decode('utf-8', errors='ignore')
                output.append(chunk)
                sys.stdout.write(chunk)
                sys.stdout.flush()
            # 读取标准错误
            if channel.recv_stderr_ready():
                sys.stderr.write(channel.recv_stderr(1024).decode('utf-8', errors='ignore'))
                sys.stderr.flush()
            if not channel.recv_ready() and not channel.recv_stderr_ready():
                time.sleep(0.01)
        return_code = channel.recv_exit_status()
        if return_code:
            logger.error(f"remote command:{cmd} exec failed, return code is {return_code}")
            logger.error(f"remote command:{cmd} exec failed, output is {''.join(output)}")
            raise Exception(f"remote command:{cmd} exec failed, output is {''.join(output)}")
        else:
            logger.info(f"remote command:{cmd} exec success, output is {''.join(output)}")
        return return_code, ''.join(output)
    except paramiko.AuthenticationException:
        logger.error("认证失败！")
        return None, None
    except paramiko.SSHException as e:
        logger.error(f"SSH连接错误: {e}")
        return None, None
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        logger.error(f"连接{ip}失败...")
        return None, None
    except socket.timeout:
        logger.error(f"连接超时：无法在10秒内连接到 {ip}")
        return None, None
    finally:
        # 关闭连接
        client.close()


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


def fio(stop_event):
    try:
        remotecmd(
            "cd /root; fio fio_perf.fio", IP, USERNAME, PASSWORD
        )
    finally:
        stop_event.set()  # fio 正常结束或异常时，结束主线程


def link_check(stop_event):
    try:
        while not stop_event.is_set():
            portcheck(serialport=SERIALPORT)
            sleep(120)
    finally:
        stop_event.set()

####main####
if __name__ == '__main__':
    stop_event = threading.Event()
    getcmdserialport()  # 获取命令串口

    t1 = threading.Thread(target=fio, args=(stop_event,), daemon=True)
    t2 = threading.Thread(target=link_check, args=(stop_event,), daemon=True)

    t1.start()
    t2.start()

    stop_event.wait()