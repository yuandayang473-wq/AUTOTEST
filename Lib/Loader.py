"""Loading unittests."""
import importlib
import os

from Lib.Case import Case, Suite
from Lib.Config import CsvLoader
from Lib.Error import TestCaseError
from Utils.GlobalConfig import InitLoadConfig


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

        # self._add_suite_params({})
        return self.suiteClass([{1: case_class}])

    def pt(self):
        return self.load_tests_from_csv_and_xmls()

    def at(self):
        return self.load_tests_from_csv_and_xmls()

    def rt(self):
        return self.load_tests_from_csv_and_xmls()

    def hib(self):
        return self.load_tests_to_csv()

    def oam(self):
        return self.load_tests_to_csv()

    def common(self):
        return self.load_tests_from_csv_and_xmls()

    def load_tests_from_csv_and_xmls(self):
        """
        根据csv 文件名，从Config 目录下查找csv 的脚本序列
        :param csv:
        :return:
        """
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        conf_path = os.path.join(root_path, "Config")

        csv = self.options.CSV

        conf = csv if csv.endswith(".csv") else csv + ".csv"
        cfg = InitLoadConfig()
        cfg.load_config(self.options.PUT)

        file = os.path.join(conf_path, conf)
        c = CsvLoader(file, ["CaseName", "Params", "Path", "Level"])
        data = c.read_csv()
        if len(data) >= 2:
            # 去掉title
            test_ins = []
            for row in data[1:]:
                # 根据导入类
                data = {}
                case_path = row['Path']
                case_name = row["CaseName"]
                case_level = 1 if row["Level"] is None else int(row["Level"])
                case_file = importlib.import_module(f"{case_path}.{case_name}")
                case_class = getattr(case_file, case_name, None)
                cmd_params = row["Params"]

                if not (case_class or issubclass(case_class, Case)):
                    raise TestCaseError(f"{case_name} not exist {case_path}/{case_name}")

                if cmd_params:
                    data = self._decode_params(row["Params"])

                common_data = self._decode_options()
                common_data.update(data)
                common_data.update(cfg.data)
                self._add_test_params(case_class, common_data)

                test_ins.append({case_level: case_class})
            suite_data = self._decode_options()
            suite_data.update(cfg.data)
            suite_data["root_path"] = root_path
            self._add_suite_params(suite_data)
            return self.suiteClass(test_ins)
        else:
            raise TestCaseError(f"CSV file tests is null")

    def load_tests_to_csv(self):
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        conf_path = os.path.join(root_path, "Config")

        csv = self.options.CSV

        conf = csv if csv.endswith(".csv") else csv + ".csv"

        file = os.path.join(conf_path, conf)
        c = CsvLoader(file, ["CaseName", "Params", "Path", "Level"])
        data = c.read_csv()
        if len(data) >= 2:
            # 去掉title
            test_ins = []
            for row in data[1:]:
                # 根据导入类
                data = {}
                case_path = row['Path']
                case_name = row["CaseName"]
                case_level = 1 if row["Level"] is None else int(row["Level"])
                case_file = importlib.import_module(f"{case_path}.{case_name}")
                case_class = getattr(case_file, case_name, None)
                cmd_params = row["Params"]
                
                if not (case_class or issubclass(case_class, Case)):
                    raise TestCaseError(f"{case_name} not exist {case_path}/{case_name}")

                if cmd_params:
                    data = self._decode_params(row["Params"])

                common_data = self._decode_options()
                common_data.update(data)
                self._add_test_params(case_class, common_data)

                test_ins.append({case_level: case_class})

            suite_data = self._decode_options()
            suite_data["root_path"] = root_path
            self._add_suite_params(suite_data)
            return self.suiteClass(test_ins)
        else:
            raise TestCaseError(f"CSV file tests is null")

    def _generate_results_csv_format_data(self, results):
        data = []
        for result in results:
            for case_lcass, result_dict in result.items():
                for index, res in result_dict.items():
                    # index: case 运行圈数， res: 是结果信息
                    err = res.get_error()
                    res = {
                        "CaseName": case_lcass + ".py",
                        "Cycle": index,
                        "Result": res.get_name(),
                        "Error": err.get_msg(),
                    }
                    data.append(res)
        return data

    def _results_write_csv(self, file_name, data):
        csv_loader = CsvLoader(file_name, fieldnames=data[0].keys())
        csv_loader.writerow_dict(data)

    def load_results_to_csv(self, file_name, results):
        data = self._generate_results_csv_format_data(results)
        self._results_write_csv(file_name, data)

    def _decode_params(self, cmd_parmas):
        data = {}
        p_list = cmd_parmas.split(":")
        for p in p_list:
            ps = p.split("=")
            data[ps[0]] = ps[1]
        return data

    def _add_test_params(self, case_class, data):

        if hasattr(case_class, "locals"):
            data = getattr(case_class, "locals")
            data.update(data)

        setattr(case_class, "locals", data)

    def _add_suite_params(self, data):
        if hasattr(self.suiteClass, "globals"):
            data = getattr(self.suiteClass, "globals")
            data.update(data)
        setattr(self.suiteClass, "globals", data)

    def _decode_options(self):
        data = {}
        for key, name in self.options.__dict__.items():
            data[key] = name
        return data
