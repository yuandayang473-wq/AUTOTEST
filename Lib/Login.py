#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   Login.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
"""

import time
import paramiko
import re
import subprocess

from Lib.Error import BmcSessionError, SshConnectionError, AuthenticationError, CmdError, PduConfError
from Lib.Constant import Status
from Lib.Result import CmdPass, CmdFail
from Lib.DataBuffer import OutData


def cmd_retry(origin_func):
    def wrapper(self, command, ignore_exit_code, save_exit_code, cmd_timeout, i_timeout_err):
        count = self.get_cmd_retry_count()
        init_val = 1
        while init_val <= count:
            try:
                rst = origin_func(self, command, ignore_exit_code, save_exit_code, cmd_timeout, i_timeout_err)
            except Exception as error:
                self.get_logger().error(error)
                msg = "Execute Command Fail,start retry %d command: %s" % (init_val, command)
                self.get_logger().error(msg)
                init_val += 1
                time.sleep(5)
                continue

            if rst.is_fail():
                if init_val >= count:
                    return rst
                msg = "Execute Command Fail,start retry %d command: %s" % (init_val, command)
                self.get_logger().error(msg)
                init_val += 1
                time.sleep(15)
                continue
            return rst

    return wrapper


class OsRunCmd:
    _instance = None

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, logger):
        self.logger = logger
        self._exit_code = 0
        self._cmd_count = 3

    def get_logger(self):
        return self.logger

    def set_logger(self, logger):
        self.logger = logger

    def get_exit_code(self):
        """
        当 run() 中参数 save_exit_code 设置True，返回当前命令的exit code
        :return:
        """
        return self._exit_code

    def get_cmd_retry_count(self):
        """
        :return: cmd 重试的次数
        """
        return self._cmd_count

    def set_cmd_retry_count(self, count):
        """
        设置 cmd 重试的次数
        :param count: int
        :return: none
        """
        self._cmd_count = count

    def run(self, command, retry_expt=3, i_exit_code=False, save_exit_code=True, timeout=3600, i_timeout_err=False,
            i_record_cmd=False, parser_type="str_parser"):
        """
        :param command: os 下执行的命令
        :param retry_expt: cmd 执行fail，重试的次数， 默认是3次
        :param i_exit_code: 忽略退出状态码， 执行命令结果按照返回状态码0为标准，命令执行返回状态码不为0，程序继续执行需要改成True
        :param i_record_cmd: 忽略当前命令记录日志中
        :param save_exit_code: 需要获得当前命令返回状态码，则设置为True，通过get_exit_code()
        :return: DataBuffer模块中 OutData 的实例对象
        """
        self.set_cmd_retry_count(retry_expt)
        if not i_record_cmd:
            self.logger.info("SSH Execute command: %s" % command)
        result = self._run(command, i_exit_code, save_exit_code, timeout, i_timeout_err)
        if result.is_fail():
            self.logger.error("Execute Command Fail, Output below \n%s" % result.get_out_rst())
            raise CmdError(f"cmd execute fail: {command}")
        # success
        parser = getattr(OutData(result.get_out_rst()), parser_type)()
        self.logger.info("SSH Execute command ok, Output below: \n%s" % parser.get_origin_data())
        return parser

    @cmd_retry
    def _run(self, command, ignore_exit_code, save_exit_code, cmd_timeout, i_timeout_err):
        returncode = Status.SUCCESS
        if not isinstance(command, str):
            raise TypeError(f'command MUST be _cmd string type, {command} is _cmd {type(command)} type')
        try:
            p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=cmd_timeout, shell=True,
                               encoding='utf-8', check=bool(1 - ignore_exit_code))
            data = p.stdout + p.stderr
            returncode = p.returncode
        except subprocess.TimeoutExpired as e:
            if i_timeout_err:
                self.logger.info(f'timeout: {cmd_timeout},auto stop cmd {command}')
                data = e
            else:
                return CmdFail(Status.FAIL, e)
        except subprocess.CalledProcessError as e:
            return CmdFail(Status.FAIL, e)

        if save_exit_code:
            self._exit_code = returncode
        return CmdPass(Status.SUCCESS, data)


class Connection:

    def __init__(self, host, username, password, logger) -> None:
        if not hasattr(self, "_host"):
            self._host = host
            self._username = username
            self._password = password
            self._logger = logger

    def get_host(self):
        return self._host

    def set_host(self, uut_ip):
        self._host = uut_ip

    def get_username(self):
        return self._username

    def get_password(self):
        return self._password

    def get_logger(self):
        return self._logger

    def set_logger(self, logger):
        self._logger = logger


class BmcConnect(Connection):

    def __init__(self, ip, user, password, mac=None, logger=None) -> None:
        super().__init__(ip, user, password, logger)
        self._mac = mac

    def get_mac(self):
        return self._mac

    def set_mac(self, mac):
        self._mac = mac

    def build_command(self, cmd):
        _str = "ipmitool -I lanplus -H {os_ip} -U {os_user} -P {os_pwd}".format(os_ip=self.get_host(),
                                                                                os_user=self.get_username(),
                                                                                os_pwd=self.get_password())

        cmd = cmd.replace("ipmitool", _str)
        return cmd

    def update_bmc_ip(self, uut):
        with SshConnect(ip=uut["ip_address"], user=uut["username"], password=uut["password"],
                        logger=self.get_logger()) as ssh:
            out_data = ssh.run("ipmitool lan print", i_exit_code=True, retry_expt=1)
            parser = out_data.str_parser()
            new_test_ip = parser.get_value(r"IP Address[ :]+((?:[0-9]+\.){3}[0-9]+)")
        self.set_host(new_test_ip)


class SshConnect(Connection):
    _instance_map = {}

    def __new__(cls, *args, **kwargs):
        single = kwargs.get('single')
        if single:
            _ip = kwargs.get('ip')
            _instance = cls._instance_map.get(_ip, None)
            if _instance is None:
                _instance = super(SshConnect, cls).__new__(cls)
                cls._instance_map[_ip] = _instance
        else:
            _instance = super(SshConnect, cls).__new__(cls)
        return _instance

    # def __init__(self, ip, user, password, port=22, logger=None, timeout=3600, login_retry=2,
    def __init__(self, ip, user, password, port=22, logger=None, login_retry=2, bmc_con=None) -> None:
        super().__init__(ip, user, password, logger)
        self.__login_count = login_retry
        # self.__timeout = timeout
        self.__cmd_count = 3
        self._bmc_con = bmc_con
        self.trans = None
        self.__exit_code = Status.SUCCESS
        self.channel = None
        self.invoke_buff = []
        self.first_invoke = True
        self.s_invoke = True
        self.__port = port

    def __enter__(self):
        count = self.get_login_retry_count()
        init_val = 1
        log = self.get_logger()
        while init_val <= count:
            try:
                #  instance a sshclient
                trans = paramiko.Transport((self.get_host(), self.__port))  # 如果你使用 paramiko.SSHClient() cd后会回到连接的初始状态
                trans.start_client()
                trans.set_keepalive(60)
                # username and password
                trans.auth_password(username=self.get_username(), password=self.get_password())
                self.trans = trans
                # get a terminal
                log.info("ssh connect success, ip: {os_ip}".format(os_ip=self.get_host()))
                return self

            except paramiko.AuthenticationException as err:
                msg = "SSH Authertication Fail,User: %s, Password: %s,start retry %d" % (
                    self.get_username(), self.get_password(), init_val)
                # self.get_logger().error(err)
                self.get_logger().info(msg)
                if init_val == count:
                    raise AuthenticationError(
                        "Authentication failed, username:%s, password:%s" % (self.get_username(), self.get_password()))

            except paramiko.SSHException as err:
                msg = "SSH Connect to %s Fail,start retry %d" % (self.get_host(), init_val)
                # self.get_logger().error(err)
                self.get_logger().info(msg)
                if init_val == count:
                    raise SshConnectionError("Unable to connect to %s" % self.get_host())

            init_val += 1
            time.sleep(60)

    def __exit__(self, exc_type, exc_value, exc_tb):
        log = self.get_logger()
        log.info("ssh Disconnect, ip: {os_ip}".format(os_ip=self.get_host()))
        if self.trans is not None:
            self.trans.close()

        if exc_type is not None:
            raise exc_value

    def get_exit_code(self):
        """
        当 run() 中参数 save_exit_code 设置True，返回当前命令的exit code
        :return:
        """
        return self.__exit_code

    def get_login_retry_count(self):
        """
        :return: ssh重连的次数
        """
        return self.__login_count

    def get_cmd_retry_count(self):
        """
        :return: cmd 重试的次数
        """
        return self.__cmd_count

    def set_cmd_retry_count(self, count):
        """
        设置 cmd 重试的次数
        :param count: int
        :return: none
        """
        self.__cmd_count = count

    # def get_timeout(self):
    #     return self.__timeout

    def set_bmc_session(self, bmc_con):
        """
        设置 bmc connetc
        :param bmc_con:
        :return:
        """
        self._bmc_con = bmc_con

    def get_bmc_session(self):
        return self._bmc_con

    def build_remote_cmd(self, cmd):
        bmc_con = self.get_bmc_session()
        if bmc_con is None:
            raise BmcSessionError("init Bmc Connection")
        remote_cmd = bmc_con.build_command(cmd)
        return remote_cmd

    def run(self, command, retry_expt=3, ipmi_I=False, i_exit_code=False, i_record_cmd=False, save_exit_code=False,
            cmd_timeout=3600, i_timeout_err=False):
        """
        :param command: os 下执行的命令
        :param retry_expt: cmd 执行fail，重试的次数， 默认是3次
        :param ipmi_I: True 开启 ipmitool -I -H -U -P [cmd] 格式
        :param i_exit_code: 忽略退出状态码， 执行命令结果按照返回状态码0为标准，命令执行返回状态码不为0，程序继续执行需要改成True
        :param i_record_cmd: 忽略当前命令记录日志中
        :param save_exit_code: 需要获得当前命令返回状态码，则设置为True，通过get_exit_code()
        :return: DataBuffer模块中 OutData 的实例对象
        """
        self.set_cmd_retry_count(retry_expt)
        if ipmi_I:
            command = self.build_remote_cmd(command)
        if not i_record_cmd:
            self.get_logger().info("SSH Execute command: %s" % command)
        result = self._run(command, i_exit_code, save_exit_code, cmd_timeout, i_timeout_err)
        if result.is_fail():
            self.get_logger().error("Execute Command Fail, Output below \n%s" % result.get_out_rst())
            raise CmdError(f"cmd execute fail: {command}")
        # success
        return OutData(result.get_out_rst())

    @cmd_retry
    def _run(self, command, ignore_exit_code, save_exit_code, cmd_timeout, i_timeout_err):
        # opne a transport
        channel = self.trans.open_session()
        # channel.settimeout(self.get_timeout())
        channel.settimeout(cmd_timeout)
        channel.get_pty()
        # try:
        channel.exec_command(command)

        # if i_timeout_err:
        #     return CmdPass(Status.SUCCESS, f'timeout: {cmd_timeout},auto stop cmd {command}')
        all_data = ""
        start_time = time.time()  # 命令开始时间
        try:
            data = channel.recv(1024).decode("utf-8")
            while data:
                all_data += data
                data = channel.recv(1024).decode("utf-8")
                end_time = time.time()
                t = int(end_time - start_time)
                # self.get_logger().info(t)
                # self.get_logger().info(cmd_timeout)
                # if int(end_time - start_time) > cmd_timeout and i_timeout_err:
                if t > cmd_timeout and i_timeout_err:
                    # if i_timeout_err:
                    self.get_logger().info(f'timeout: {cmd_timeout},auto stop cmd {command}')
                    return CmdPass(Status.SUCCESS, all_data)
                time.sleep(1)
        except Exception as err:
            # data = channel.recv(1024).decode("utf-8")
            # all_data += data
            if i_timeout_err:
                self.get_logger().info(f'timeout: {cmd_timeout},auto stop cmd {command}')
                return CmdPass(Status.SUCCESS, all_data)
        status_code = channel.recv_exit_status()
        channel.close()

        if ignore_exit_code:
            return CmdPass(Status.SUCCESS, all_data)

        if save_exit_code:
            self.__exit_code = status_code
            return CmdPass(Status.SUCCESS, all_data)

        if status_code == Status.SUCCESS:
            return CmdPass(Status.SUCCESS, all_data)

        return CmdFail(Status.FAIL, all_data)

    def start_invoke(self):
        if self.channel is None:
            channel = self.trans.open_session()
            channel.get_pty()
            channel.invoke_shell()
            self.channel = channel

    def end_invoke(self):
        self.channel.close()
        del self.channel
        self.channel = None
        self.s_invoke = True

    def get_invoke_buff(self):
        data = "".join(self.invoke_buff)
        self.invoke_buff = []
        return data

    def invoke_run(self, command, end_with="# ", manual_stop=False, timeout=60):
        channel = self.channel
        cmd = command + "\n"
        channel.send(cmd)
        buff = ''
        ret = re.search(end_with, buff, re.I | re.M)
        self.get_logger().info(f"ret : {ret}")
        value = 1
        while ret is None:
            resp = channel.recv(2048)
            buff += resp.decode('utf-8')
            if manual_stop:
                time.sleep(value)
                break
            time.sleep(value)
            ret = re.search(end_with, buff, re.I | re.M)
            self.get_logger().info(f"ret : {ret}")
            if value >= timeout:
                break
            value += 1

        if self.first_invoke:
            if buff.count(command) > 1:
                buffs = buff.split(command, 1)
                buff = buffs[1] if len(buffs) >= 2 else buffs[0]

            self.first_invoke = False

        if manual_stop:
            buff = "null"

        self.invoke_buff.append(buff)

    def invoke(self, cmd, end_with="# ", manual_stop=False, end_invoke=False, timeout=60):
        """
        交互式运行
        :param cmd: os 系统命令
        :param end_with: 结束标志
        :param manual_stop: 手动停止等待结束标志
        :param end_invoke: 结束交互模式
        :return: DataBuffer.OutData 实例对象
        """
        if self.s_invoke:
            self.start_invoke()
            self.s_invoke = False

        self.invoke_run(cmd, end_with, manual_stop, timeout)

        if end_invoke:
            self.end_invoke()
            return OutData(self.get_invoke_buff())

        return None

    def remote_scp(self, src, des):
        """
        :param src: 远程目标文件
        :param des: 本地目标文件
        :return: None
        """
        self.get_logger().info(f"SFTP remote file:{src}, local file: {des}")
        stfp = paramiko.SFTPClient.from_transport(self.trans)
        stfp.get(src, des)
        stfp.close()

    def local_scp(self, src, des):
        """
        :param src: 本地目标文件
        :param des: 远程目标文件
        :return:
        """
        self.get_logger().info(f"SFTP local file:{src}, remote file: {des}")
        stfp = paramiko.SFTPClient.from_transport(self.trans)
        stfp.put(src, des)
        stfp.close()


class ApcConnect:

    def __init__(self, ip, pdu_mode, port, logger=None) -> None:
        self.ip = ip
        self.pdu_model = pdu_mode
        self.port = port
        self.logger = logger
        self.count = 3

    def check_field(self, field):
        if field is None or field == "":
            raise PduConfError(f"PDU config is error")
        return field

    def pdu_on(self, obj):
        for snmpget, snmpset in self._snmpget_set(status="on"):
            self._ac_action(obj, snmpget, snmpset, "on")

    def pdu_off(self, obj):
        for snmpget, snmpset in self._snmpget_set(status="off"):
            self._ac_action(obj, snmpget, snmpset, "off")

    def _snmpget_set(self, status):
        port = self.check_field(self.port)
        port_list = port.split()
        on_list = []
        for p in port_list:
            set_cmd = f'snmpset -v 1 -c private {self.ip} {self.pdu_model}.{p}.0 s "{status}"'
            time.sleep(2)
            set_cmd = f'snmpset -v 1 -c private {self.ip} {self.pdu_model}.{p}.0 s "{status}"'
            get_cmd = f'snmpget -v 1 -c private {self.ip} {self.pdu_model}.{p}.0 s'
            on_list.append((get_cmd, set_cmd))
        return on_list

    def _ac_action(self, obj, snmpget, snmpset, status):
        obj.execute_run(snmpset)
        time.sleep(2)
        parser = obj.execute_run(snmpget, i_exit_code=True)
        pattern = f'STRING: "{status}"'
        if parser.check_field(pattern):
            return None
        else:
            count = 3
            while count > 0:
                time.sleep(10)
                parser = obj.execute_run(snmpget, i_exit_code=True)
                if parser.check_field(pattern):
                    return None
                count -= 1

            while self.count > 0:
                self.count -= 1
                self._ac_action(obj, snmpget, snmpset, status)


if __name__ == '__main__':
    pass
