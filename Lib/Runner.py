"""Running tests"""
from Lib.Loader import TestLoader
from Protocal_test.test_rst_mep_flr import Mep_Flr
from Protocal_test.test_sbr_loop import SbrLoop

from Protocal_test.test_link_speed_change import SpeedChange
from reboot import reboot
from a import test_a


class TestRunner(object):

    def __init__(self):
        self.suite = None

    def runner(self, case_list):
        test_loader = TestLoader()
        self.suite = test_loader.load_tests_from_name(case_list)
        self.suite.suite_run()


runner = TestRunner()
runner.runner([test_a])
