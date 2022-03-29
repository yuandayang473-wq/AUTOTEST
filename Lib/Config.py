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

from .Error import KeyNotExistError, MyFileNotFounTError, CSVPermissionError, OverrideError


class LoadConfig(object):
    def __init__(self, cfg_path_name, cfg_name):
        super(LoadConfig, self).__init__()
        self.cfg_path_name = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), cfg_path_name)
        self.cfg_name = cfg_name
        self.file_path = None
        self.cnf = None

    def _load_config(self, config_path):
        raise OverrideError("must be override load_config()")

    def _dump_config(self, config_path, data):
        raise OverrideError("must be override dump_config()")

    def get_config(self):
        if self.cnf is None:
            self.cnf = self._load_config(self.get_path())
        return self.cnf

    def dump_config(self, data, is_new_file=False):
        file = os.path.join(self.cfg_path_name, self.cfg_name) if is_new_file else self.get_path()
        self._dump_config(file, data)

    def get_path(self):
        if self.file_path:
            return self.file_path
        if self.file_path is None:
            for root, dirs, files in os.walk(self.cfg_path_name):
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

    def _load_config(self, config_path) -> dict:
        with open(config_path, 'r', encoding="utf-8") as f:
            conf = f.read()
            cnf = yaml.load(conf, Loader=yaml.FullLoader)
            return cnf

    def _dump_config(self, config_path, data):
        config_path = self.get_path()
        with open(config_path, 'w', encoding="utf-8") as f:
            yaml.dump(data, f)


class JsonLoadConfig(LoadConfig):

    def __init__(self, cfg_path_name="Config", cfg_name="result.yaml"):
        super().__init__(cfg_path_name=cfg_path_name, cfg_name=cfg_name)

    def _load_config(self, config_path) -> dict:
        with open(config_path, "r", encoding="utf-8") as f:
            cnf = json.loads(f.read())
            return cnf

    def data(self, key):
        data = self.get_config()
        keys = key.split(".")
        if len(keys) > 1:
            for key in keys:
                data = data[key]
        else:
            data = data[key]
        return data

    def _dump_config(self, config_path, data):
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=4, sort_keys=False, ensure_ascii=False) + '\n')


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
