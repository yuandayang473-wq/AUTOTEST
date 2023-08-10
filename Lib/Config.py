#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   Config.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
"""
import yaml
import json
import os
import csv
from xml.dom import minidom as xmldom
import requests

from .Error import KeyNotExistError, MyFileNotFounTError, CSVPermissionError, OverrideError


class Config:
    """A Config instance contains the configuration of a test.
    """

    def __init__(self, path: str):
        # The configuration raw data.
        self.__data = {}

        # Load configuration from file.
        self.__load_yaml(path)

    def __str__(self):
        return "%s" % (self.__data)

    def __load_yaml(self, path: str):
        """Load a YAML configuration file.

        :param path: the YAML file path
        :type path: str
        """
        yaml.warnings({'YAMLLoadWarning': False})
        with open(path, "r", encoding='utf-8') as f:
            raw = f.read()
            self.__data = yaml.full_load(raw)

    def find(self, path: str):
        """Find data in the configuration.

        :param path: the key path separated by dot, such as 'a.b.c'
        :type path: str
        :return: the value found in the configuration
        :raises KeyError: If the path doesn't exist, raise a KeyError.
        :rtype: depends on the value found in the configuration
        """
        nodes = path.split(".")
        value = self.__data
        for node in nodes:
            value = value[node]
        return value


class LoadConfig(object):
    def __init__(self, cfg_path_name, cfg_name):
        super(LoadConfig, self).__init__()
        self.project_config = os.environ.get("CLIENT_NAME")
        self.cfg_path_name = cfg_path_name
        self.cfg_name = cfg_name
        self.file_path = None
        self.cnf = None

    def load_config(self, config_path):
        raise OverrideError("must be override load_config()")

    def get_config(self):
        if self.cnf is None:
            self.cnf = self.load_config(self.get_path())
        # if self.cnf is None:
        #     self.cnf = self.load_config_from_nacos(self.cfg_name)

        return self.cnf

    def get_path(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.cfg_path_name)
        if self.project_config is not None:
            holding_path = os.path.join(
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.cfg_path_name),
                self.project_config)
            if os.path.exists(holding_path):
                config_path = holding_path
        if self.file_path is None:
            for root, dirs, files in os.walk(config_path):
                if self.cfg_name in files:
                    self.file_path = os.path.join(root, self.cfg_name)
                    break
        if self.file_path is None:
            for root, dirs, files in os.walk(os.path.join(config_path, os.path.pardir)):
                if self.cfg_name in files:
                    self.file_path = os.path.join(root, self.cfg_name)
                    break
        if self.file_path is None:
            raise MyFileNotFounTError("{} file not found".format(self.cfg_name))
        return self.file_path


class YamlLoadConfig(LoadConfig):

    def __init__(self, cfg_path_name="Config", cfg_name="Device.yaml"):
        super().__init__(cfg_path_name=cfg_path_name, cfg_name=cfg_name)

    def data(self, config_key):
        value = None
        cnf = self.get_config()
        if isinstance(cnf, dict):
            value = cnf.get(config_key, None)
        if value is None:
            raise KeyNotExistError("{} not exist".format(config_key))
        return value

    def load_config(self, config_path) -> dict:
        with open(config_path, 'r', encoding="utf-8") as f:
            conf = f.read()
            cnf = yaml.load(conf, Loader=yaml.FullLoader)
            return cnf

    def load_config_from_nacos(self, config_name) -> dict:
        nacos_server = os.environ.get("NACOS_SERVER", "10.67.13.25:8848")
        res = requests.get(f"http://{nacos_server}/nacos/v1/cs/configs?dataId={config_name}&group=DEFAULT_GROUP")
        if res.status_code == 200:
            conf = res.text
            cnf = yaml.load(conf, Loader=yaml.FullLoader)
            return cnf
        return None

    def yaml_dump(self, data):
        config_path = self.get_path()
        with open(config_path, 'w', encoding="utf-8") as f:
            yaml.dump(data, f)


class JsonLoadConfig(LoadConfig):

    def __init__(self, cfg_path_name="Config", cfg_name="Device.yaml"):
        super().__init__(cfg_path_name=cfg_path_name, cfg_name=cfg_name)

    def load_config(self, config_path) -> dict:
        with open(config_path, "r", encoding="utf-8") as f:
            cnf = json.loads(f.read())
            return cnf

    def data(self, type_name):
        pass

    def dump_config(self, data):
        with open(self.get_path(), "w", encoding="utf-8") as f:
            f.write(json.dumps(data))


class CsvLoader:

    def __init__(self, csv_path, fieldnames):
        self.file = csv_path
        self.fieldnames = fieldnames
        self._write_header(self.file)

    def load_config(self, config_path):
        pass

    def _write_header(self, file):
        if not os.path.isfile(file):
            with open(file, "w", newline="", encoding='utf-8-sig') as f:
                f_csv = csv.writer(f)
                f_csv.writerow(self.fieldnames)

    def writerow_dict(self, data, fieldnames=None):
        # create csv file
        if fieldnames is None:
            fieldnames = self.fieldnames
        try:
            with open(self.file, 'a', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerows(data)
        except PermissionError:
            raise CSVPermissionError("please colse {}".format(self.file))
        except FileNotFoundError:
            raise FileNotFoundError("Can not access {}".format(self.file))

    def read_csv(self, fieldnames=None):
        data = []
        if fieldnames is None:
            fieldnames = self.fieldnames
        try:
            with open(self.file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile, fieldnames=fieldnames)
                for row in reader:
                    data.append(row)
            return data
        except PermissionError:
            raise CSVPermissionError("please colse {}".format(self.file))
        except FileNotFoundError:
            raise FileNotFoundError("Can not access {}".format(self.file))


class XmlLoadder(LoadConfig):

    def __init__(self, cfg_path_name="Lib/BiosLib", cfg_name="Bios.xml") -> None:
        super().__init__(cfg_path_name, cfg_name)

    def load_config(self, config_path):
        dom_obj = xmldom.parse(config_path)
        ele_obj = dom_obj.documentElement
        homes = ele_obj.getElementsByTagName("home")
        # 遍历每个元素
        from xml.dom.minidom import Document
        from xml.dom.minidom import Element
        from xml.dom.minicompat import NodeList
        for home in homes:
            print(type(home))
            print(home.getElementsByTagName("name")[0].firstChild.data)

    def feild_data(self, name, ele):
        tag_ele = ele.getElementsByTagName(name)[0]
        try:
            field = tag_ele.firstChild.data
            if "<p>" in field:
                field = field.replace("<p>", "").replace("</p>", "")
            if "<ol>" in field:
                field = field.replace("<ol>", "").replace("</ol>", "")
            if "<li>" in field:
                field = field.replace("<li>", "").replace("</li>", "")
        except AttributeError:
            field = "none"
        return field


if __name__ == "__main__":
    pass
