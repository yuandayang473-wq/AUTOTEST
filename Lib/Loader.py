"""Loading unittests."""
import importlib
import os

from Lib.Case import Case, Suite
from Lib.Config import CsvLoader
from Lib.Error import TestCaseError
from Utils.Init import InitLoadConfig


class TestLoader(object):
    """
    This class is responsible for loading tests according to various criteria
    and returning them wrapped in a TestSuite
    """

    suiteClass = Suite

    def __init__(self, options=None):
        self.options = options

    def load_tests_from_name(self, case_class: str):
        if not (case_class or issubclass(case_class, Case)):
            raise TestCaseError(f"{case_class} is must Item subclass ")

        return self.suiteClass([case_class])

