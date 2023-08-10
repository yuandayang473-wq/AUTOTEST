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

import time
import logging
import os
import sys
import difflib

from .Result import Result, Fail, Undefined
from .Error import Error, ErrItemFail, MyAssertError
from .Config import YamlLoadConfig
from .Constant import PASS_TITLE, FAIL_TITLE
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

        self.__primary_result = Undefined(self)

        self.__results = []

        # The start time of the case.
        self.__start_time = None

        # The end time of the case.
        self.__end_time = None

        self.__id = None

        self.__expect = None

        self.__sleep = SleepTime()
        self._step = Step()

        # 依赖其他case的结果信息
        self.depend_result = None

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
        # self.__logger = logger.getChild(self.__name)
        # setattr(self.__logger, "sh", logger.sh)
        # setattr(self.__logger, 'log_name', logger.log_name)
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

    def run(self) -> Result:
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
        # retstr += ("Bucket Name:  %s\n" % os.environ['BUCKET_NAME'])
        retstr += ("Log Name:     %s\n" % self.get_logger().get_name())
        return retstr

    def end_to_string(self, result: Result):
        _time = time.strftime('%H:%M:%S', time.gmtime(self.get_duration()))
        retstr = "\n------------------------ Test Case %d summary -----------------------\n" % self.ID
        retstr += "ID:            %d\n" % self.ID
        retstr += ("Name:         %s\n" % self.name)
        retstr += ("Expect:       %s\n" % self.expect)
        retstr += ("Test_Result:  %s\n" % result.get_name())
        retstr += ("Case Time:    %s\n" % _time)
        return retstr

    def end_to_error_string(self, result: Result):
        err_result = self.end_to_string(result)
        err_result += ("Error:        %s\n" % result.get_error())
        return err_result

    def set_global_params(self, key, value):
        """
        设置全局变量参数
        :param key: 属性
        :param value: 值
        :return:
        """
        pass


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

    def run(self) -> Result:
        logger = self.get_logger()
        step = Step()
        step.set_logger(logger=self.get_logger())
        try:
            self.update_start_time()
            # loglevel = self.logger.sh.level
            # self.logger.sh.setLevel(10)
            logger.info(self.head_to_string())
            # self.logger.sh.setLevel(loglevel)
            self.setup()
            ret = self.exe()
            self.tearDown()
            self.update_end_time()
            # self.get_logger().sh.setLevel(10)
            step.log_step_result(step.step_num) if hasattr(step, "step_num") else None
            msg = self.end_to_error_string(ret) if isinstance(ret, Fail) else self.end_to_string(ret)
            logger.info(msg)
        except (AssertionError, Error) as err:
            self.update_end_time()
            step.log_step_result(step.step_num, "FAILED") if hasattr(step, "step_num") else None
            self.get_logger().error(err)
            ret = Fail(self, err)
            try:
                self.tearError()
            except Error as err:
                logger.info(err.get_msg())

            # self.get_logger().sh.setLevel(10)
            logger.error(self.end_to_error_string(ret))

        return ret

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

    def fail(self, msg=None):
        """Fail immediately, with the given message."""
        raise self.failureException(msg)

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

    def assertIsInstance(self, title, obj, cls):
        """Same as self.assertTrue(isinstance(obj, cls)), with a nicer
        default message."""
        if isinstance(obj, cls):
            msg = '%s is an instance of %r' % (str(obj), cls)
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is not an instance of %r' % (str(obj), cls)
            self.fail(self._fail_title(title, msg))

    def assertEqual(self, title, current_val, expect_val):
        """Fail if the two objects are unequal as determined by the '=='
           operator.
        """
        if current_val == expect_val:
            self.success(self._success_compare_msg(title, current_val, expect_val))
        else:
            self.fail(self._fail_compare_msg(title, current_val, expect_val))

    def assertNotEqual(self, title, current_val, expect_val):
        """Fail if the two objects are equal as determined by the '!='
           operator.
        """
        if current_val != expect_val:
            self.success(self._success_not_compare_msg(title, current_val, expect_val))
        else:
            self.fail(self._success_not_compare_msg(title, current_val, expect_val))

    def assertIsNone(self, title, obj):
        """Same as self.assertTrue(obj is None), with a nicer default message."""
        if obj is None:
            msg = '%s is None' % (self._auto_line_feed(obj),)
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is not None' % (self._auto_line_feed(obj),)
            self.fail(self._fail_title(title, msg))

    def assertIsNotNone(self, title, obj):
        """Included for symmetry with assertIsNone."""
        if obj is not None:
            msg = '%s is not None' % (self._auto_line_feed(obj),)
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is None' % (self._auto_line_feed(obj),)
            self.fail(self._fail_title(title, msg))

    def assertIn(self, title, member, container):
        """Just like self.assertTrue(a in b), but with a nicer default message."""
        if member in container:
            msg = '%s found in %s' % (self._auto_line_feed(member), self._auto_line_feed(container))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not found in %s' % (self._auto_line_feed(member), self._auto_line_feed(container))
            self.fail(self._fail_title(title, msg))

    def assertNotIn(self, title, member, container):
        """Just like self.assertTrue(a not in b), but with a nicer default message."""
        if member not in container:
            msg = '%s not found in %s' % (self._auto_line_feed(member), self._auto_line_feed(container))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s found in %s' % (self._auto_line_feed(member), self._auto_line_feed(container))
            self.fail(self._fail_title(title, msg))

    def assertIs(self, title, expr1, expr2):
        """Just like self.assertTrue(a is b), but with a nicer default message."""
        if expr1 is expr2:
            msg = '%s is %s' % (self._auto_line_feed(expr1), self._auto_line_feed(expr2))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is not %s' % (self._auto_line_feed(expr1), self._auto_line_feed(expr2))
            self.fail(self._fail_title(title, msg))

    def assertIsNot(self, title, expr1, expr2):
        """Just like self.assertTrue(a is not b), but with a nicer default message."""
        if expr1 is not expr2:
            msg = '%s is not %s' % (self._auto_line_feed(expr1), self._auto_line_feed(expr2))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s is %s' % (self._auto_line_feed(expr1), self._auto_line_feed(expr2))
            self.fail(self._fail_title(title, msg))

    def assertLess(self, title, a, b):
        """Just like self.assertTrue(a < b), but with a nicer default message."""
        a = self._str2_float(a)
        b = self._str2_float(b)
        if a < b:
            msg = '%s less than %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not less than %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.fail(self._fail_title(title, msg))

    def assertLessEqual(self, title, a, b):
        """Just like self.assertTrue(a <= b), but with a nicer default message."""
        a = self._str2_float(a)
        b = self._str2_float(b)
        if a <= b:
            msg = '%s less than or equal to %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not less than or equal to %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.fail(self._fail_title(title, msg))

    def assertGreater(self, title, a, b):
        """Just like self.assertTrue(a > b), but with a nicer default message."""
        a = self._str2_float(a)
        b = self._str2_float(b)
        if a > b:
            msg = '%s greater than %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not greater than %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.fail(self._fail_title(title, msg))

    def assertGreaterEqual(self, title, a, b):
        """Just like self.assertTrue(a >= b), but with a nicer default message."""
        a = self._str2_float(a)
        b = self._str2_float(b)
        if a >= b:
            msg = '%s greater than or equal to %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.success(self._success_title(title, msg))
        else:
            msg = '%s not greater than or equal to %s' % (self._auto_line_feed(a), self._auto_line_feed(b))
            self.fail(self._fail_title(title, msg))

    def assertFalse(self, title, expr):
        """Check that the expression is false."""
        if not expr:
            msg = "%s is false" % self._auto_line_feed(expr)
            self.success(self._success_title(title, msg))
        else:
            msg = "%s is not false" % self._auto_line_feed(expr)
            self.fail(self._fail_title(title, msg))

    def assertTrue(self, title, expr):
        """Check that the expression is true."""
        if expr:
            msg = "%s is true" % self._auto_line_feed(expr)
            self.success(self._success_title(title, msg))
        else:
            msg = "%s is not true" % self._auto_line_feed(expr)
            self.fail(self._success_title(title, msg))

    def _truncateMessage(self, message, diff):
        max_diff = self.maxDiff
        if max_diff is None or len(diff) <= max_diff:
            return message + diff
        return message + (DIFF_OMITTED % len(diff))

    def assertMultiLineEqual(self, first, second, msg=None):
        """Assert that two multi-line strings are equal."""
        self.assertIsInstance(first, str, 'First argument is not a string')
        self.assertIsInstance(second, str, 'Second argument is not a string')

        if first != second:
            # don't use difflib if the strings are too long
            if (len(first) > self._diffThreshold or
                    len(second) > self._diffThreshold):
                self._baseAssertEqual(first, second, msg)
            firstlines = first.splitlines(keepends=True)
            secondlines = second.splitlines(keepends=True)
            if len(firstlines) == 1 and first.strip('\r\n') == first:
                firstlines = [first + '\n']
                secondlines = [second + '\n']
            standardMsg = '%s != %s' % _common_shorten_repr(first, second)
            diff = '\n' + ''.join(difflib.ndiff(firstlines, secondlines))
            standardMsg = self._truncateMessage(standardMsg, diff)
            self.fail(self._formatMessage(msg, standardMsg))


class Suite:
    """A Suite instance executes several test cases."""

    root_logger = None
    global_config = None

    def __init__(self, tests=()):
        # The name of a suite.
        self.__name = "Unit Test"

        # self.__options = None
        # The children of a suite. All Children must be a Case or a sub-class of Case.
        self._tests = {}  # { level: []}
        self._errors = []
        self.__results = []

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
        for test in tests:
            self.add_test(test)

    def add_test(self, case: dict):
        """
        :param case: {level:case()}
        :return:
        """
        for key, test in case.items():
            if not issubclass(test, Item):
                raise ErrItemFail(f"{test.__name__} inherit Item object")

            test.parent = self
            if key in self._tests.keys():
                self._tests[key].append(test)
            else:
                self._tests[key] = [test]

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

    def get_result(self):
        return self.__results

    def set_result(self, ret: dict):
        """Set the test result.

        :param ret: the test result
        :type ret: Result
        """
        self.__results.append(ret)

    def run(self, mode):
        # 记录开始时间
        self.update_start_time()

        if mode == "debug":
            self._run(self._tests.get(1, []))
        else:
            # 0 预处理
            tests = self._tests.get(0, [])
            result = self._run(tests)
            if result is not None:
                self.print_fail()
            # 1 正常执行
            result = self._run(self._tests.get(1, []))
            if result:
                self._errors.append(result)
                # self.print_fail()
            else:
                # 获取脚本执行的结果
                for result in self.get_result():
                    for case_name, results in result.items():
                        for index, res in results.items():
                            if res.is_fail():
                                self._errors.append(res)

        if self._errors:
            # 3 脚本执行失败执行动作
            self._run(self._tests.get(3, []))
            self.print_fail()
        else:
            # 2 脚本序列执行成功，执行动作
            self._run(self._tests.get(2, []))
            self.print_pass()

        # 记录结束时间
        self.update_end_time()

    def _run(self, tests):
        case_results = {}

        for test in tests:
            instance = test()
            prefix_format = self.globals.get("log_prefix", None)
            case_cycle = self.globals.get("CaseCycle", 1)
            log_flag = self.globals.get("LogFlag", "debug")
            case_logger = self.root_logger.case_logger(test.__name__, prefix_format, log_flag)
            instance.set_logger(case_logger)
            results = {}
            for c in range(1, case_cycle + 1):
                instance.ID = c
                # case 圈数大于1是添加分隔符
                # if c > 1:
                #     split_line = "=" * 25 + str(c) + "=" * 25 + "\n"
                #     case_logger.info(split_line)
                ret = instance.run()
                ret.ID = c
                results[c] = ret

                # 当前case 执行失败，是否继续执行
                if hasattr(test, "locals"):
                    CaseFailStop = test.locals["CaseFailStop"]
                else:
                    CaseFailStop = self.globals["CaseFailStop"]

                if ret.is_fail() and CaseFailStop.lower() == "yes":
                    case_results[test.__name__] = results
                    self.set_result(case_results)
                    return ret

            case_results[test.__name__] = results
        self.set_result(case_results)
        return None

    def single_run(self):
        self.update_start_time()
        self.create_root_logger()
        for key, tests in self._tests.items():
            for test in tests:
                instance = test()
                case_logger = self.root_logger.case_logger(test.__name__, None, "debug")
                instance.set_logger(case_logger)
                instance.ID = key
                ret = instance.run()
                ret.ID = instance.ID
                self.set_result(ret)
                if ret.is_fail():
                    self.print_fail()
        # 记录结束时间
        self.update_end_time()

    def summary(self):
        pass_count, fail_count, p_IDs, f_IDs = self.collect_case()
        _time = time.strftime('%H:%M:%S', time.gmtime(self.get_duration()))
        retstr = "\n=============== Test summary ==============\n"
        retstr += "Test Suite Name:    %s\n" % self.name
        retstr += "Total Case:         %d\n" % len(self._tests)
        retstr += "Run Case:           %d\n" % len(self.__results)
        retstr += "Passed:             %d\n" % pass_count
        retstr += "Failed:             %d\n" % fail_count
        retstr += "Passed IDs:         %s\n" % str(p_IDs)
        retstr += "Failed IDs:         %s\n" % str(f_IDs)
        retstr += "Total Time:         %s" % _time

        return retstr

    def collect_case(self):
        pass_count = 0
        fail_count = 0
        p_IDs = []
        f_IDs = []
        for result in self.__results:
            if result.is_pass():
                pass_count += 1
                p_IDs.append(result.ID)
            else:
                fail_count += 1
                f_IDs.append(result.ID)
        return pass_count, fail_count, p_IDs, f_IDs

    def print_pass(self):
        self.print_termial(PASS_TITLE)

    def print_fail(self):
        self.print_termial(FAIL_TITLE)

    def print_summary(self):
        self.print_termial(self.summary())

    def print_termial(setlf, msg):
        time.sleep(1)
        sys.stdout.write(msg + "\n")
