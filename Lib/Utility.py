#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@ins-ict.com
@Software:   V2
@File    :   Utility.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©ins  2022 . All Rights Reserved.
@Desc    :   None
"""

import time
from Lib.logger import Logger
LOGGER = Logger()
from Lib.Config import YamlLoadConfig
import os

def singleton(cls):
    """A decorator to make a class a Singleton."""
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

@singleton
class SleepTime:

    def __call__(self, sec):
        LOGGER.info(f"sleep {sec}s")
        time.sleep(sec)

@singleton
class ConfigDeal:

    def __init__(self):
        self.__config = {}

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
            if "folder" in conf:
                c = YamlLoadConfig(cfg_path_name=conf["folder"], cfg_name=conf["file"])
            else:
                c = YamlLoadConfig(cfg_name=conf["file"])

            if "key" in conf:
                if isinstance(conf["key"], dict):
                    data = conf["key"]
                else:
                    keys = conf["key"].split("/")
                    if len(keys) > 1:
                        data = c.data(keys[0])
                        for key in keys[1:]:
                            data = data[key]
                        else:
                            self._gen_tool_abspath(keys, data)
                    else:
                        if "." in conf["key"]:
                            keys = conf["key"].split(".")
                            data = c.get_config()
                            for key in keys:
                                data = data[key]
                        else:
                            data = c.data(keys[0])
            else:
                data = c.get_config()

            self.__config[conf["name"]] = data
    def _gen_tool_abspath(self, keys, data):
        for k, v in data.items():
            if isinstance(v, str):
                # data[k] = os.path.join(self.root_path, "/".join(keys), v)
                data[k] = os.path.join("/run/LuxScript", "/".join(keys), v)
            else:
                keys.append(k)
                self._gen_tool_abspath(keys, data[k])
                keys.pop(keys.index(k))

if __name__ == '__main__':
    pass
