#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   DataBuffer.py
@Time    :   2022/8/17
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
"""

import platform
import re

MATCH_FAIL = 'Null'


# load_list = ["PPU"]
#
#
# def load_package(path):
#     parent_folder = os.path.dirname(path)
#     for dirname in os.listdir(parent_folder):
#         if dirname in load_list:
#             sys.path.append(os.path.join(parent_folder, dirname))
#             load_list.pop(load_list.index(dirname))
#         if not load_list:
#             return None
#     else:
#         return load_package(parent_folder)
#
#
# load_package(os.path.abspath(__file__))


class Parser:

    def get_origin_data(self):
        """This is a virtual method."""
        pass


class RawParse:

    def __init__(self, data) -> None:
        #  data = "20 81 00 60 02 bf 1c c6 00 df 15 00 00 00 00"
        self.__data = bytearray.fromhex(data.strip())

    def get_unit8(self, offset):
        """[根据偏移量获取对应的数值]
        Args:
            offset ([int]): 索引值
        Returns:
            [int]: [十六进制对应的十进制数]
        """
        return self.__data[offset]

    def get_unit16(self, offset, mode="little"):
        """[根据Little-endian 模式返回16进制的对应的数值]
        Args:
            offset ([int]): [索引值]
            mode  (str): little/ big
        Returns:
            [int]: [十六进制对应的十进制数]
        Example:
            get_unit16(0) -> 0x8120
        """
        return int.from_bytes(self.__data[offset:offset + 2], mode)

    def set_unit16(self, offset, value):
        self.__data[offset:offset + 2] = value.to_bytes(2, 'little')

    def get_bit(self, offset=0, bit_offset=0, length=1):
        """
        Args:
            offset (int, optional): [偏移量]. Defaults to 0.
            bit_offset (int, optional): [按位右移动多少位数]. Defaults to 0.
            length (int, optional): [位的长度]. Defaults to 1.

        Returns:
            [int]: [返回按位与的结果值]
        """
        return (self.get_unit8(offset=offset) >> bit_offset) & (2 ** length - 1)


class DataRawParse(Parser, RawParse):

    def __init__(self, data) -> None:
        # data:  b'20 81 01 20 02 bf 1c c6 00 e1 15 00 00 00 00'
        super().__init__(data)
        self.__data_list = self._raw(data)

    def _raw(self, data):
        byte_list = data.strip().split()
        return byte_list

    def raw_data(self, index):
        return int(self.__data_list[index], 16)

    def raw_offset_data(self, start, offset, reverse=True):
        end = start + offset + 1
        data_line = ""
        new_list = []
        for index in range(start, end):
            data = self.__data_list[index]
            if reverse:
                new_list.insert(0, data)
            else:
                new_list.append(data)

        for d in new_list:
            data_line += d
        return int(data_line, 16)

    def get_origin_data(self):
        new_list = []
        for data in self.__data_list:
            new_list.append(data)
        return " ".join(new_list)

    def raw_length(self):
        return len(self.__data_list)

    def get_data_list(self):
        return self.__data_list

    def raw_str(self, index):
        return self.__data_list[index]


class StrParser(Parser):

    def __init__(self, data=None) -> None:
        if isinstance(data, bytes):
            self.data = str(data, encoding="utf-8")
        if isinstance(data, str):
            self.data = data

        if platform.system().lower() == 'windows':
            self.data = self.data.replace("\r", "")

    def _get_data(self, match, flag=True):
        """
        complie : Match string
        flag : exist Capture group
        """
        result = MATCH_FAIL
        res = re.search(match, self.data, re.I | re.M)
        if res is None:
            return result
        if flag:
            result = res.group(1).strip()
        else:
            result = res.group().strip()
        return result

    def check_field(self, match):
        """ 检查字段信息是否存在数据中
        :param match: 匹配信息
        :return: boolean
        """
        fr = self._get_data(match, flag=False)
        if fr is MATCH_FAIL:
            return False
        return True

    def get_value(self, match):
        """
        匹配字符串中的数据
        :param match: 正则表达式
        :return: str/None
        """
        result = self._get_data(match)
        # if result == MATCH_FAIL:
        #     raise ReMatchFail(f"re match fail, re expression:{match}")
        return result

    def get_origin_data(self):
        """
        :return: 原始字符串数据
        """
        if self.data:
            return self.data.strip()
        return MATCH_FAIL

    def filter_value(self, match):
        """
        匹配字符串中的多个数据
        :param match: 正则表达式
        :return: str/None
        """
        res_list = re.findall(match, self.data, re.I)
        res = MATCH_FAIL
        if res_list:
            res = "\n".join(res_list)
        return res

    def filter_list(self, match):
        """
        匹配字符串中的多个数据
        :param match: 正则表达式
        :return: list/None
        """
        res_list = re.findall(match, self.data, re.I)
        res = []
        if res_list:
            res = res_list
        return res

    def counts(self, match):
        """
        匹配字符串中的字段出现次数
        :param match:
        :return:
        """
        res_list = re.findall(match, self.data, re.I)
        res = 0
        if res_list:
            res = len(res_list)
        return res

    def split(self, pattern):
        res_list = re.split(pattern, self.data, flags=re.I)
        return res_list


class SolStrParser(StrParser):

    def __init__(self, data=None) -> None:
        if isinstance(data, bytes):
            data = bytes.decode(data)
        else:
            data = str(data)
        self.data = re.sub(r"(?:\\x1b\[[01]+;[0-9]+;[0-9]+m)|(?:\\x1b\[[0-9]+;[0-9]+H)", "", data)

    def show_data(self, data=None):
        if isinstance(data, bytes):
            data = bytes.decode(data)
        else:
            data = str(data)
        data = re.sub(r"(?:\\x1b\[[01]+;[0-9]+;[0-9]+m)|(?:\\x1b\[[0-9]+;[0-9]+H)", "", str(data))
        return "\n".join(data.split("||"))


class OutData:

    def __init__(self, data) -> None:
        self.__data = data

    def raw_parser(self):
        """
        :return: DataRawParse 实例对象
        """
        return DataRawParse(self.__data)

    def str_parser(self):
        """
        :return: StrParser 实例对象
        """
        return StrParser(self.__data)


if __name__ == '__main__':
    data = """"""
    p = StrParser(data)
    val = p.get_value(r"Chassis Part Number[: ]+(\w+)\.\w+")
    print(val)

