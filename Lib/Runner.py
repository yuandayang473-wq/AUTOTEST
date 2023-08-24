"""Running tests"""
from Lib.Loader import TestLoader


class TestRunner(object):

    def __init__(self):
        self.suite = None

    def single_runner(self, name):
        test_loader = TestLoader()
        self.suite = test_loader.load_tests_from_name(name)
        self.suite.single_run()


runner = TestRunner()
