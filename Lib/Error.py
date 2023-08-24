#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   Error.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
"""
from .Constant import ErrCode, Status


class Error(Exception):

    def __init__(self, message, status, *args: object) -> None:
        super().__init__(*args)
        self.__message = message
        self.__status = status

    def __str__(self) -> str:
        return "status code:{}, message:{}".format(self.get_status(), self.get_msg())

    def get_msg(self):
        return self.__message

    def get_status(self):
        return self.__status


class ErrItemFail(Error):
    """An ErrItemFail instance logs a test item failure."""

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.ITEM, *args)


class ErrSuiteFail(Error):
    """An ErrSuiteFail instance logs a test suite failure."""

    def __init__(self, message, *args: object):
        Error.__init__(self, ErrCode.SUITE, message)


class ErrNone(Error):
    """An ErrNone instance logs that no failure happened.
    """

    def __init__(self, message="ErrorNone", *args: object):
        super().__init__(self, Status.SUCCESS, message)

    def __str__(self) -> str:
        return ""


class EofError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.EOF, *args)


class TimeoutError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.TIMEOUT, *args)


class SshConnectionError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.SSH_CONNECTION, *args)


class AuthenticationError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.AUTHENTICATION, *args)


class FormatError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.FORMAT, *args)


class KeyNotExistError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.KEY_NOT_EXIST, *args)


class OverrideError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.OVERRIDE, *args)


class MyFileNotFounTError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.FileNotFound, *args)


class InitParamsError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.INIT_PARAMS, *args)


class CSVPermissionError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.PERMISSION_ERROR, *args)


class SSHSessionError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.SSH_SESSION, *args)


class BmcSessionError(Error):
    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.BMC_SESSION, *args)


class NotFindElementError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.ELEMENT_NOT_FOUND, *args)


class MyValueError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.VALUE_ERROR, *args)


class CmdError(Error):

    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.CMD, *args)


class ReMatchFail(Error):
    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.RE_MATCH_FAIL, *args)


class MyAssertError(Error):
    def __init__(self, type_code, message, *args: object):
        super().__init__(message, type_code, *args)


class PduConfError(Error):
    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.PDU_CONF_ERROR, *args)


class TestCaseError(Error):
    def __init__(self, message, *args: object):
        super().__init__(message, ErrCode.TEST_CASE_ERROR, *args)
