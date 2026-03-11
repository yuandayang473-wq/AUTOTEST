#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@ins-ict.com
@Software:   V2
@File    :   Constant.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©ins  2022 . All Rights Reserved.
@Desc    :   None
"""
import re


class Status:
    SUCCESS = 0
    FAIL = 1


class ErrCode:
    EOF = -1
    TIMEOUT = -2
    FORMAT = -3
    KEY_NOT_EXIST = -4
    OVERRIDE = -5
    FileNotFound = -6
    INIT_PARAMS = -7
    PERMISSION_ERROR = -8
    SSH_SESSION = -9
    BMC_SESSION = -10
    SSH_CONNECTION = -11
    AUTHENTICATION = -12
    ELEMENT_NOT_FOUND = -13
    VALUE_ERROR = -14
    ITEM = -15
    SUITE = -16
    CMD = -17
    POWER_CHECK = -18
    RE_MATCH_FAIL = -19
    MY_ASSERT_ERROR = -20
    PDU_CONF_ERROR = -21
    TEST_CASE_ERROR = -22


class Log:
    name = "lux_test"
    debug = "debug"
    normal = "normal"



