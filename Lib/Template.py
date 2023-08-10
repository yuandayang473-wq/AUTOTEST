#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   Template.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
"""


import contextlib

from .Case import Item
from .Error import OverrideError, SSHSessionError, TimeoutError
from Utils.Login import SshConnect, BmcConnect
from Cmd.Cmd import get_bios_boot_stage, Chassis, build_cmd
from Utils.DataBuffer import StrParser


class TempItem(Item):

    def __init__(self):
        super(TempItem, self).__init__()
        # Expected PN
        # The max retry number.
        self.ssh = None
        self._errors_flag = False
        self.errors = []
        self.__options = None

    @property
    def options(self):
        return self.__options

    @options.setter
    def options(self, options):
        self.__options = options

    @property
    def logger(self):
        return self.get_logger()

    def exe(self):
        """Run the case.
        This is a virtual method.

        :return: the test result
        :rtype: Result
        """
        raise OverrideError("Must be Override exe()")

    def execute_run(self, cmd, parser_type="str_parser", logger=None, **kwargs) -> StrParser:
        """
        :param cmd: os 系统命令
        :param parser_type:  解析器类型 [str_parser/raw_parser], 默认 str_parser
        :param kwargs:  Login.SshConnect.run 中的参数 retry_expt=3, ipmi_I=False, i_exit_code=False, i_record_cmd=False,
                        save_exit_code=False,cmd_timeout=3600,i_timeout_err 参数详解看 Login.SshConnect.run
        :return: DataBuffer.StrParser/DataBuffer.RawParser 实例对象
        """
        if self.ssh is None:
            raise SSHSessionError("init self.ssh")
        desc = kwargs.pop("desc", False)

        logger = self.get_logger() if logger is None else logger
        if desc and desc != "":
            logger.info(f"{cmd} description info: {desc}")

        out_data = self.ssh.run(cmd, **kwargs)
        parser = getattr(out_data, parser_type)()
        i_record_cmd = kwargs.get("i_record_cmd", False)
        if not i_record_cmd:
            logger.info("SSH Execute command ok, Output below: \n%s" % parser.get_origin_data())

        return parser

    def outband_run(self, cmd, parser_type="str_parser", logger=None, **kwargs) -> StrParser:
        kwargs.update({"ipmi_I": True})
        return self.execute_run(cmd, parser_type=parser_type, logger=logger, **kwargs)

    def invoke_run(self, cmd, parser_type="str_parser", **kwargs):
        """
        交互式运行
        :param cmd: os 系统命令
        :param parser_type: 解析器类型 [str_parser/raw_parser], 默认 str_parser
        :param kwargs: Login.SshConnect.invoke 中的参数 end_with="# ", manual_stop=False, end_invoke=False
        :return: DataBuffer.StrParser/DataBuffer.RawParser 实例对象
        """
        if self.ssh is None:
            raise SSHSessionError("init self.ssh")
        out_data = self.ssh.invoke(cmd, **kwargs)
        if out_data:
            parser = getattr(out_data, parser_type)()
            self.get_logger().info("SSH Execute command ok, Output below: \n%s" % parser.get_origin_data())
            return parser
        return out_data

    @contextlib.contextmanager
    def ssh_connect(self, uut=None, login_retry=20):
        """默认连接bmc 的os"""
        if uut is None:
            uut = self.config["BMC"]
        with SshConnect(ip=uut["ip_address"], user=uut["username"], password=uut["password"],
                        port=uut.get("port", 22), logger=self.logger, login_retry=login_retry) as ssh:
            self.ssh = ssh
            yield

    @contextlib.contextmanager
    def ssh_outband_connect(self, uut=None, bmc=None, login_retry=20):
        if uut is None:
            uut = self.config["LOCAL"]
        if bmc is None:
            bmc = self.config["BMC"]
        bmc_con = BmcConnect(ip=bmc["ip_address"], user=bmc["username"], password=bmc["password"],
                             logger=self.get_logger())
        with SshConnect(ip=uut["ip_address"], user=uut["username"], password=uut["password"], port=uut.get("port", 22),
                        logger=self.logger, login_retry=login_retry, bmc_con=bmc_con) as ssh:
            self.ssh = ssh
            yield

    @contextlib.contextmanager
    def action(self, level):
        self.logger.info("=" * 30 + f"start {level} action" + "=" * 30)
        try:
            yield
        except Exception as err:
            raise err
        finally:
            self.logger.info("=" * 30 + f"end {level} action" + "=" * 30)

    def tips_msg(self, msg):
        return f"[编号: {self.parent.globals['log_prefix']}]--{msg}"


class BiosTmepItem(TempItem):

    def setup(self):
        with self.action("check entry os"):
            with self.ssh_outband_connect():
                parser = self.outband_run(Chassis.power_status)
                value = parser.get_value(r"Chassis Power is (on|off)")
                if value == "on":
                    self.outband_run(Chassis.power_reset)
                else:
                    self.outband_run(Chassis.power_on)

                self.check_bios_boot_stage(ipmi_I=True)

    def check_bios_boot_stage(self, count=20, ipmi_I=False):
        cur_count = 0
        while cur_count <= count:
            parser = self.execute_run(build_cmd(get_bios_boot_stage, "0x00 0x4c 0xa5"), parser_type="raw_parser",
                                      desc="get bios boot stage", ipmi_I=ipmi_I)
            val = parser.get_unit8(0)
            if val == 200:
                break
            self.sleep(20)
        else:
            raise TimeoutError("not check bios boot stage")

