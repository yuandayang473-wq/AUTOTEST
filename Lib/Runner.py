"""Running tests"""
import os
from optparse import OptionParser

from Lib.Config import YamlLoadConfig
from Lib.Loader import TestLoader


class TestRunner(object):

    def __init__(self):
        self.suite = None

    def batch_runner(self, mode="release"):
        self.options = self._init_cmd_options()
        test_loader = TestLoader(self.options)

        csv = self.options.CSV
        stage = csv[:-4] if csv.endswith(".csv") else csv

        stage = stage.lower()
        if hasattr(test_loader, stage):
            func = getattr(test_loader, stage.lower())
        else:
            func = getattr(test_loader, "common")

        # self.suite = test_loader.load_tests_from_csv_and_xmls()
        self.suite = func()
        self.init_test_run_env(mode)
        log_path = self.suite.root_logger.LOG_ROOT_PATH
        prefix = self.suite.globals.get("log_prefix", None)
        if prefix:
            file_name = os.path.join(log_path, f"{prefix}_reports.csv")
        else:
            file_name = os.path.join(log_path, "reports.csv")

        test_loader.load_results_to_csv(file_name, self.suite.get_result())

    def single_runner(self, name):
        test_loader = TestLoader()
        self.suite = test_loader.load_tests_from_name(name)
        # self.init_test_run_env(mode)
        self.suite.single_run()

    def init_test_run_env(self, mode):
        # print(self.suite.globals)
        # folder=self.suite.globals["folder"]
        self.suite.create_root_logger()
        self.suite.run(mode)

    def _init_cmd_options(self, extend_para=[]):
        optparser = OptionParser()
        if extend_para:
            for p_file, p_dict in extend_para:
                c = YamlLoadConfig(p_file)
                i_p = p_dict.get("include", [])
                e_p = p_dict.get("exclude", [])
                default_p = p_dict.get("default", {})

                if not i_p:
                    params = c.get_config()
                    i_p = params.keys()

                p_list = set(i_p) - set(e_p)

                for section in p_list:
                    para = c.data(section)
                    if section in default_p:
                        para["default"] = default_p[section]
                    optparser.add_option('--' + str(section), **para)
        else:
            cnf = YamlLoadConfig(cfg_name="Param.yaml")
            common_para = cnf.get_config()
            for section, value in common_para.items():
                optparser.add_option('--' + str(section), **value)
        options, args = optparser.parse_args()
        return options


runner = TestRunner()
