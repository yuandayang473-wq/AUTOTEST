#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   Result.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
"""

import time

from .Error import Error, ErrNone


class Result:
    """A Result instance contains the test result of a test item, test group,
    test suite or other objects.
    """

    def __init__(self, name, worker):
        # The result name.
        self.__name = name

        # The worker is the creator of the result.
        self.__worker = worker

        # Assume the worker is a test case. If the __pass is True, the test
        # case pass. Otherwise the test case fail.
        self.__pass = False

        # The error logs the failure type and message.
        self.__error = ErrNone()

        # The timestamp logs the Result instance created time.
        self.__id = None

    def __str__(self):
        worker = self.get_worker()
        _time = time.strftime('%H:%M:%S', time.gmtime(worker.get_duration()))
        s = "Name: {}, Timestamp: {}, Result: {}, Error: {}".format(
            worker.name, _time, self.__name, self.__error)
        return s

    def get_name(self) -> str:
        """Get the name of the Reuslt.

        :return: the name of the Result.
        :rtype: str
        """
        return self.__name

    def get_worker(self) -> str:
        """Get the worker object.

        :return: the worker
        :rtype: str
        """
        return self.__worker

    def is_pass(self) -> bool:
        """Return true if the test pass, otherwise return false.

        :return: True or False
        :rtype: bool
        """
        return self.__pass

    def is_fail(self) -> bool:
        """Return true if the test fail, otherwise return false.

        :return: True or False
        :rtype: bool
        """
        return not self.__pass

    def set_error(self, is_pass: bool, err: Error):
        """Set the error.

        :param is_pass: pass/fail
        :type is_pass: bool
        :param err: the error
        :type err: Error
        """
        self.__pass = is_pass
        self.__error = err

    def get_error(self) -> Error:
        """Get the error.

        :return: the error
        :rtype: Error
        """
        return self.__error

    def update_timestamp(self):
        """Update the timestamp to now.
        """
        self.__timestamp = time.time()

    @property
    def ID(self):
        return self.__id

    @ID.setter
    def ID(self, cycle_id):
        self.__id = cycle_id


class Pass(Result):
    """A Pass instance indicates a test pass."""

    def __init__(self, worker):
        Result.__init__(self, "Passed", worker)
        self.set_error(True, ErrNone())


class Fail(Result):
    """A Fail instance indicates a test fail."""

    def __init__(self, worker, err: Error):
        Result.__init__(self, "Failed", worker)
        self.set_error(False, err)


class Undefined(Result):
    """An Undefined instance indicates the test result is undefined.
    Generally this means a test hasn't started.
    """

    def __init__(self, worker):
        Result.__init__(self, "Undefined", worker)
        self.set_error(False, ErrNone())


class CmdResult:

    def __init__(self, code, rst) -> None:
        self.__code = code
        self.__rst = rst
        self.__pass = True

    def is_fail(self):
        return not self.__pass

    def set_flag(self, flag):
        self.__pass = flag

    def get_out_rst(self):
        return self.__rst

    def get_code(self):
        return self.__code


class CmdPass(CmdResult):

    def __init__(self, code, rst) -> None:
        super().__init__(code, rst)
        self.set_flag(True)


class CmdFail(CmdResult):

    def __init__(self, code, rst) -> None:
        super().__init__(code, rst)
        self.set_flag(False)
