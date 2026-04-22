#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@ins-ict.com
@Software:   V2
@File    :   Template.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©ins  2022 . All Rights Reserved.
@Desc    :   None
"""

import contextlib
import json
import os
import re
import time

import yaml

from .Error import OverrideError, SSHSessionError
from .Login import SshConnect, BmcConnect, OsRunCmd
from .DataBuffer import StrParser
from collections import namedtuple, defaultdict

from .Utility import singleton
from .logger import Logger

LOGGER = Logger()

@singleton
class Base:

    def __init__(self):
        # Expected PN
        # The max retry number.
        self.ssh = None
        self._errors_flag = False
        self.errors = []


    def execute_run(self, cmd, parser_type="str_parser", **kwargs) -> StrParser:
        """
        :param cmd: os 系统命令
        :param parser_type:  解析器类型 [str_parser/raw_parser], 默认 str_parser
        :param kwargs:  Login.SshConnect.run 中的参数 retry_expt=3, ipmi_I=False, i_exit_code=False, i_record_cmd=False,cmd_timeout=3600,i_timeout_err 参数详解看 Login.SshConnect.run
        :return: DataBuffer.StrParser/DataBuffer.RawParser 实例对象
        """
        if self.ssh is None:
            raise SSHSessionError("init self.ssh")
        desc = kwargs.pop("desc", False)

        if desc and desc != "":
            LOGGER.info(f"{cmd} description info: {desc}")

        out_data = self.ssh.run(cmd, **kwargs)
        parser = getattr(out_data, parser_type)()
        i_record_cmd = kwargs.get("i_record_cmd", False)
        if not i_record_cmd:
            LOGGER.info("SSH Execute command ok, Output below: \n%s" % parser.get_origin_data())

        return parser

    def outband_run(self, cmd, parser_type="str_parser", **kwargs) -> StrParser:
        kwargs.update({"ipmi_I": True})
        return self.execute_run(cmd, parser_type=parser_type, **kwargs)

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
            LOGGER.info("SSH Execute command ok, Output below: \n%s" % parser.get_origin_data())
            return parser
        return out_data

    @contextlib.contextmanager
    def ssh_connect(self, uut=None, login_retry=20):
        """默认连接bmc 的os"""
        if uut is None:
            uut = self.config["BMC"]
        with SshConnect(ip=uut["ip"], user=uut["username"], password=uut["password"],
                        port=uut.get("port", 22), logger=LOGGER, login_retry=login_retry) as ssh:
            self.ssh = ssh
            yield

    @contextlib.contextmanager
    def ssh_outband_connect(self, uut=None, bmc=None, login_retry=20):
        if uut is None:
            uut = self.config["LOCAL"]
        if bmc is None:
            bmc = self.config["BMC"]
        bmc_con = BmcConnect(ip=bmc["ip_address"], user=bmc["username"], password=bmc["password"],
                             logger=LOGGER)
        with SshConnect(ip=uut["ip_address"], user=uut["username"], password=uut["password"], port=uut.get("port", 22),
                        logger=LOGGER, login_retry=login_retry, bmc_con=bmc_con) as ssh:
            self.ssh = ssh
            yield

    @property
    def os_run(self):
        return OsRunCmd(logger=LOGGER)

