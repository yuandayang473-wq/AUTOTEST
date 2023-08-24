#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   Case.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
"""
import contextlib
import time
import logging
import os

from Lib.Constant import Log
from .Result import Pass, Fail, Result
from .Error import Error, ErrItemFail, MyAssertError
from .Config import YamlLoadConfig, JsonLoadConfig
from .Utility import SleepTime, Step
from .Logging import LoggerFactory, CaseLogger

_MAX_LENGTH = 100
_LIEN_FEED_LENGTH = 60
DIFF_OMITTED = ('\nDiff is %s characters long. '
                'Set self.maxDiff to None to see it.')


def safe_repr(obj, short=False):
    try:
        result = repr(obj)
    except Exception:
        result = object.__repr__(obj)
    if not short or len(result) < _MAX_LENGTH:
        return result
    return result[:_MAX_LENGTH] + ' [truncated]...'


def _common_shorten_repr(*args):
    args = tuple(map(safe_repr, args))
    maxlen = max(map(len, args))
    if maxlen <= _MAX_LENGTH:
        return args


class Case:
    """Test Case"""

    def __init__(self):

        # The case name.
        self.__name = None

        self.__config = {}

        self.__logger = None

        # The start time of the case.
        self.__start_time = None

        # The end time of the case.
        self.__end_time = None

        self.__id = None

        self.__expect = None

        self.__sleep = SleepTime()
        self._step = Step()

        self.isSkip = False
        self.result = Pass(self)

    @property
    def ID(self):
        return self.__id

    @ID.setter
    def ID(self, cycle_id):
        self.__id = cycle_id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name: str):
        self.__name = name

    @property
    def expect(self):
        return self.__expect

    @expect.setter
    def expect(self, expect: str):
        self.__expect = expect

    @property
    def sleep(self):
        """
        :return: SleepTime instance
        """
        return self.__sleep

    @sleep.setter
    def sleep(self, logger):
        """
        :return: SleepTime instance
        """
        self.__sleep.set_logger(logger=logger)

    @property
    def step(self):
        """
        :return: SleepTime instance
        """
        return self._step

    @step.setter
    def step(self, logger):
        """
        :return: SleepTime instance
        """
        self._step.set_logger(logger=logger)

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, confs: list):
        """解析参数
        [
            {
                "file": "config.yaml",
                "folder": "Config",
                "name": "config"
                "value": "$config:boot"
            },
        ]
        """
        for conf in confs:
            if isinstance(conf["key"], dict):
                data = conf["key"]
            else:
                if "folder" in conf and conf:
                    c = YamlLoadConfig(cfg_path_name=conf["folder"], cfg_name=conf["file"])
                else:
                    c = YamlLoadConfig(cfg_name=conf["file"])

                if "key" in conf:
                    data = c.data(conf["key"])

                else:
                    data = c.get_config()

            self.__config[conf["name"]] = data

    def get_logger(self) -> CaseLogger:
        """Get the logger.

        :raises ValueError: If the logger hasn't set, raise a ValueError.
        :return: the logger
        :rtype: logging.Logger
        """
        if self.__logger == None:
            raise ValueError("not found logger")
        return self.__logger

    def set_logger(self, logger: CaseLogger):
        """Set the logger.
        :param logger: a Logging.CaseLogger instance
        :type logger: logging.Logger
        :raises ValueError: If the logger isn't a Logging.CaseLogger, raise a ValueError.
        """
        if not isinstance(logger, CaseLogger):
            raise ValueError("invalid logger type")
        self.__logger = logger
        self.sleep = self.step = logger

    def get_start_time(self) -> float:
        """Get the start time.

        :return: the start time
        :rtype: float
        """
        return self.__start_time

    def get_start_time_strfmt(self) -> str:
        """Get te start time in string format.

        :return: the start time
        :rtype: str
        """
        if self.__start_time == None:
            return ""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.__start_time))

    def update_start_time(self):
        """Update the start time to now.
        """
        self.__start_time = time.time()

    def get_end_time(self) -> float:
        """Get the end time.

        :return: the end time
        :rtype: float
        """
        return self.__end_time

    def get_end_time_strfmt(self) -> str:
        """Get te end time in string format.

        :return: the end time
        :rtype: str
        """
        if self.__end_time == None:
            return ""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.__end_time))

    def update_end_time(self):
        """Update the end time to now.
        """
        self.__end_time = time.time()

    def get_duration(self) -> float:
        """Get the test duration. If start time or end time is None, it returns zero.

        :return: the duration
        :rtype: float
        """
        if self.__start_time != None and self.__end_time != None:
            return self.__end_time - self.__start_time
        return 0

    def run(self):
        """Run the case.
        This is a virtual method.

        :return: the test result
        :rtype: Result
        """
        pass

    def exe(self):
        """Run the case.
        This is a virtual method.

        :return: the test result
        :rtype: Result
        """
        pass

    def setup(self):
        """ initialize before run the case
        """
        pass

    def tearDown(self):
        """initialize after run the case
        """
        pass

    def tearError(self):
        pass

    def head_to_string(self):
        retstr = "\n----------- Test Case %d Start----------\n" % self.ID
        retstr += "ID:           %d\n" % self.ID
        retstr += ("Name:         %s\n" % self.name)
        retstr += ("Expect:       %s\n" % self.expect)
        retstr += ("Log Name:     %s\n" % self.get_logger().get_name())
        return retstr

    def _temp_result(self):
        _time = time.strftime('%H:%M:%S', time.gmtime(self.get_duration()))
        retstr = "\n------------------------ Test Case %d summary -----------------------\n" % self.ID
        retstr += "ID:            %d\n" % self.ID
        retstr += ("Name:         %s\n" % self.name)
        retstr += ("Expect:       %s\n" % self.expect)
        retstr += ("Test_Result:  %s\n" % self.result.get_name())
        retstr += ("Case Time:    %s\n" % _time)
        return retstr

    def _temp_error_result(self):
        result = self._temp_result()
        err_result = ""
        for typeCode, err_msg in self.result.errors:
            err_result += ("Error:        [%s: %s]\n" % (typeCode, err_msg))
        return result + err_result

    def show_result(self):
        errors = self.result.errors
        if errors:
            return self._temp_error_result()
        return self._temp_result()


class Item(Case):
    """Test Item"""

    # failureException = AssertionError
    failureException = MyAssertError
    _diffThreshold = 2 ** 16
    maxDiff = 80 * 8

    def __init__(self):
        super().__init__()
        self.__parent = None

    @property
    def parent(self):
        """Get the parent.

        :return: the parent
        :rtype: Suite or Group
        """
        return self.__parent

    @parent.setter
    def parent(self, p):
        self.__parent = p

    def run(self):
        logger = self.get_logger()
        step = Step()
        step.set_logger(logger=self.get_logger())
        try:
            self.update_start_time()
            logger.info(self.head_to_string())
            self.setup()
            ret = self.exe()
            if ret is not None:
                errors = self.result.errors
                self.result = ret
                self.result.errors.extend(errors)

            self.tearDown()
            self.update_end_time()
            step.log_step_result(step.step_num) if hasattr(step, "step_num") else None
        except (AssertionError, Error) as err:
            self.update_end_time()
            step.log_step_result(step.step_num, "FAILED") if hasattr(step, "step_num") else None
            self.get_logger().error(err)
            errors = self.result.errors
            self.result = Fail(self, err)
            self.result.errors.extend(errors)
            try:
                self.tearError()
            except Error as err:
                logger.info(err.get_msg())

        logger.info(self.show_result())

        return self.result

    def _auto_line_feed(self, data):

        def safe_repr(obj):
            try:
                result = repr(obj)
            except Exception:
                result = object.__repr__(obj)
            if len(result) < _MAX_LENGTH:
                return result
            return result[:_MAX_LENGTH] + ' [truncated]...'

        data = safe_repr(data)

        if len(data) > _LIEN_FEED_LENGTH:
            return "\n" + data + "\n"
        return data

    def str_length_auto_line(self, data):
        self.get_logger().info(data)
        new_data = []
        l = len(data)
        max_length = _MAX_LENGTH
        start_length = 0
        while l > max_length:
            new_data.append(data[start_length:max_length])
            start_length = max_length
            max_length += _MAX_LENGTH

        new_data.append(data[start_length:])

        return "\n".join(new_data)

    def _str2_float(self, a):
        if isinstance(a, str):
            return float(a)
        return a

    def _title(self, title, result, msg):
        return f"{title} check {result}! \n output result: {msg}"

    def _fail_title(self, title, msg):
        return self._title(title, "fail", msg)

    def _success_title(self, title, msg):
        return self._title(title, "pass", msg)

    def _compare_result_msg(self, title, result, current_val, expect_val):
        return f"{title} compare {result}! \ncurrent result: {current_val}, expect result: {expect_val}"

    def _compare_not_result_msg(self, title, result, current_val, expect_val):
        return f"{title} compare {result}! \ncurrent result: {current_val}, expect not result: {expect_val}"

    def _fail_compare_msg(self, title, current_val, expect_val):
        return self._compare_result_msg(title, "fail", self._auto_line_feed(current_val),
                                        self._auto_line_feed(expect_val))

    def fail(self, typeCode, msg=None):
        """Fail immediately, with the given message."""
        if self.isSkip:
            self.result.errors.append((typeCode, msg))
        else:
            raise self.failureException(typeCode, msg)

    def _success_compare_msg(self, title, current_val, expect_val):
        return self._compare_result_msg(title, "success", self._auto_line_feed(current_val),
                                        self._auto_line_feed(expect_val))

    def _success_not_compare_msg(self, title, current_val, expect_val):
        return self._compare_not_result_msg(title, "fail", self._auto_line_feed(current_val),
                                            self._auto_line_feed(expect_val))

    def success(self, msg):
        self.get_logger().info(msg)

    def _baseAssertEqual(self, title, current_val, expect_val):
        """The default assertEqual implementation, not type specific."""
        if not current_val == expect_val:
            self.fail(self._fail_compare_msg(title, current_val, expect_val))

    def assertIsInstance(self, typeCode, title, obj, cls):
        """Same as self.assertTrue(isinstance(obj, cls)), with a nicer
        default message."""
        if isinstance(obj, cls):
            msg = '%s is an instance of %r' % (str(obj), cls)
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is not an instance of %r' % (str(obj), cls)
            self.fail(typeCode, self._fail_title(title, msg))

    def assertEqual(self, typeCode, title, current_val, expect_val):
        """Fail if the two objects are unequal as determined by the '=='
           operator.
        """
        if current_val == expect_val:
            self.success(self._success_compare_msg(title, current_val, expect_val))
        else:
            self.fail(typeCode, self._fail_compare_msg(title, current_val, expect_val))

    def assertNotEqual(self, typeCode, title, current_val, expect_val):
        """Fail if the two objects are equal as determined by the '!='
           operator.
        """
        if current_val != expect_val:
            self.success(self._success_not_compare_msg(title, current_val, expect_val))
        else:
            self.fail(typeCode, self._success_not_compare_msg(title, current_val, expect_val))

    def assertIsNone(self, typeCode, title, obj):
        """Same as self.assertTrue(obj is None), with a nicer default message."""
        if obj is None:
            msg = '%s is None' % (self._auto_line_feed(obj),)
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is not None' % (self._auto_line_feed(obj),)
            self.fail(typeCode, self._fail_title(title, msg))

    def assertIsNotNone(self, typeCode, title, obj):
        """Included for symmetry with assertIsNone."""
        if obj is not None:
            msg = '%s is not None' % (self._auto_line_feed(obj),)
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is None' % (self._auto_line_feed(obj),)
            self.fail(typeCode, self._fail_title(title, msg))

    def assertIn(self, typeCode, title, member, container):
        """Just like self.assertTrue(a in b), but with a nicer default message."""
        if member in container:
            msg = '%s found in %s' % (self._auto_line_feed(member), self._auto_line_feed(container))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not found in %s' % (self._auto_line_feed(member), self._auto_line_feed(container))
            self.fail(typeCode, self._fail_title(title, msg))

    def assertNotIn(self, typeCode, title, member, container):
        """Just like self.assertTrue(a not in b), but with a nicer default message."""
        if member not in container:
            msg = '%s not found in %s' % (self._auto_line_feed(member), self._auto_line_feed(container))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s found in %s' % (self._auto_line_feed(member), self._auto_line_feed(container))
            self.fail(typeCode, self._fail_title(title, msg))

    def assertIs(self, typeCode, title, expr1, expr2):
        """Just like self.assertTrue(a is b), but with a nicer default message."""
        if expr1 is expr2:
            msg = '%s is %s' % (self._auto_line_feed(expr1), self._auto_line_feed(expr2))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is not %s' % (self._auto_line_feed(expr1), self._auto_line_feed(expr2))
            self.fail(typeCode, self._fail_title(title, msg))

    def assertIsNot(self, typeCode, title, expr1, expr2):
        """Just like self.assertTrue(a is not b), but with a nicer default message."""
        if expr1 is not expr2:
            msg = '%s is not %s' % (self._auto_line_feed(expr1), self._auto_line_feed(expr2))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is %s' % (self._auto_line_feed(expr1), self._auto_line_feed(expr2))
            self.fail(typeCode, self._fail_title(title, msg))

    def assertLess(self, typeCode, title, a, b):
        """Just like self.assertTrue(a < b), but with a nicer default message."""
        a = self._str2_float(a)
        b = self._str2_float(b)
        if a < b:
            msg = '%s less than %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not less than %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.fail(typeCode, self._fail_title(title, msg))

    def assertLessEqual(self, typeCode, title, a, b):
        """Just like self.assertTrue(a <= b), but with a nicer default message."""
        a = self._str2_float(a)
        b = self._str2_float(b)
        if a <= b:
            msg = '%s less than or equal to %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not less than or equal to %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.fail(typeCode, self._fail_title(title, msg))

    def assertGreater(self, typeCode, title, a, b):
        """Just like self.assertTrue(a > b), but with a nicer default message."""
        a = self._str2_float(a)
        b = self._str2_float(b)
        if a > b:
            msg = '%s greater than %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not greater than %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.fail(typeCode, self._fail_title(title, msg))

    def assertGreaterEqual(self, typeCode, title, a, b):
        """Just like self.assertTrue(a >= b), but with a nicer default message."""
        a = self._str2_float(a)
        b = self._str2_float(b)
        if a >= b:
            msg = '%s greater than or equal to %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not greater than or equal to %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.fail(typeCode, self._fail_title(title, msg))

    def assertFalse(self, typeCode, title, expr):
        """Check that the expression is false."""
        if not expr:
            msg = "%s is false" % self._auto_line_feed(expr)
            self.success(self._success_title(title, msg))
        else:
            msg = "%s is not false" % self._auto_line_feed(expr)
            self.fail(typeCode, self._fail_title(title, msg))

    def assertTrue(self, typeCode, title, expr):
        """Check that the expression is true."""
        if expr:
            msg = "%s is true" % self._auto_line_feed(expr)
            self.success(self._success_title(title, msg))
        else:
            msg = "%s is not true" % self._auto_line_feed(expr)
            self.fail(typeCode, self._success_title(title, msg))

    def _truncateMessage(self, message, diff):
        max_diff = self.maxDiff
        if max_diff is None or len(diff) <= max_diff:
            return message + diff
        return message + (DIFF_OMITTED % len(diff))

    @contextlib.contextmanager
    def skip_error(self):
        self.isSkip = True
        yield
        self.isSkip = False


class Suite:
    """A Suite instance executes several test cases."""

    root_logger = None
    global_config = None

    def __init__(self, tests=()):
        # The name of a suite.
        self.__name = "Unit Test"

        # self.__options = None
        # The children of a suite. All Children must be a Case or a sub-class of Case.
        self._tests = []  # []

        # The start time of the suite.
        self.__start_time = None

        # The end time of the suite.
        self.__end_time = None

        self.add_tests(tests)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name: str):
        self.__name = name

    def add_tests(self, tests):
        if isinstance(tests, str):
            raise TypeError("tests must be an iterable of tests, not a string")
        self.add_test(tests)

    def add_test(self, case: list):
        """
        :param case: [case]
        :return:
        """
        for test in case:
            if not issubclass(test, Item):
                raise ErrItemFail(f"{test.__name__} inherit Item object")

            test.parent = self
            self._tests.append(test)

    def get_tests(self):
        return self._tests

    def create_root_logger(self, folder=None, sub_folder=None):
        self.root_logger = LoggerFactory.generate_logger(folder, sub_folder)

    def update_root_logger(self, folder=None, sub_folder=None):
        # self.root_logger = LoggerFactory.generate_logger()
        self.root_logger.update_root_logger(folder, sub_folder)

    def get_start_time(self) -> float:
        """Get the start time.

        :return: the start time of the suite
        :rtype: float
        """
        return self.__start_time

    def get_start_time_strfmt(self) -> str:
        """Get te start time in string format.

        :return: the start time
        :rtype: str
        """
        if self.__start_time == None:
            return ""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.__start_time))

    def update_start_time(self):
        """Update the start time to now.
        """
        self.__start_time = time.time()

    def get_end_time(self) -> float:
        """Get the end time.

        :return: the end time of the suite
        :rtype: float
        """
        return self.__end_time

    def update_end_time(self):
        """Update the end time to now.
        """
        self.__end_time = time.time()

    def get_end_time_strfmt(self) -> str:
        """Get te end time in string format.

        :return: the end time
        :rtype: str
        """
        if self.__end_time == None:
            return ""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.__end_time))

    def get_duration(self) -> float:
        """Get the duration of the suite. It retruns zero if the start time is
        None or the end time is None.

        :return: the duration of the suite
        :rtype: float
        """
        if self.__start_time != None and self.__end_time != None:
            return self.__end_time - self.__start_time
        return 0

    def single_run(self):
        self.update_start_time()
        self.create_root_logger()
        test_id = 1
        # for test in self._tests:
        test = self._tests[0]
        instance = test()
        # case_logger = self.root_logger.case_logger(test.__name__, None, Log.normal)
        case_logger = self.root_logger.case_logger(Log.name, None, Log.debug)
        instance.set_logger(case_logger)
        instance.ID = test_id
        ret = instance.run()
        ret.ID = instance.ID
        # 记录结束时间
        self.update_end_time()
        self.generate_test_report(ret)

    def generate_test_report(self, ret: Result):
        temp_ret = {
            "logfile": os.path.join(self.root_logger.LOG_ROOT_PATH, "lux_test.log"),
            "logfolder": self.root_logger.LOG_ROOT_PATH,
        }

        if ret.is_pass():
            temp_ret["result"] = "PASS"
        else:
            temp_ret["result"] = "FAIL"
            errlist = []
            for typeCode, err_msg in ret.errors:
                errlist.append({
                    "errcode": typeCode,
                    "errmsg": err_msg
                })

            temp_ret["errlist"] = errlist

        JsonLoadConfig(cfg_path_name="", cfg_name="result.json").set_config(temp_ret, is_new_file=True)
