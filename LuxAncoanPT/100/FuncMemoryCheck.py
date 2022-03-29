# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncMemoryCheck.py
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/Memory测试  （机头）
'''
import os
import sys


load_list = ["PPU"]


def load_package(path):
    parent_folder = os.path.dirname(path)
    for dirname in os.listdir(parent_folder):
        if dirname in load_list:
            sys.path.append(os.path.join(parent_folder, dirname))
            load_list.pop(load_list.index(dirname))
        if not load_list:
            return None
    else:
        return load_package(parent_folder)


load_package(os.path.abspath(__file__))

from Lib.Result import Pass
from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.DataBuffer import StrParser


class FuncMemoryCheck(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "memory"
        self.expect = "This is memory function check test on the server"

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"folder": "LuxAncoanPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.parent.globals["RK"]},
        ]

    def exe(self):
        server = self.config["cfg"]["SERVER"]
        e_memory_count = server["mem_count"]
        e_memory_size = server["mem_size"]
        # e_memory_speed = mem_config["Speed"]
        memory_count = 0
        with self.ssh_connect(uut=self.config["UUT"]):
            self.step(1, "get memory info")
            parser = self.execute_run(
                r"""dmidecode -t 17 |awk 'BEGIN{RS="Memory Device\n";FS="\n"}{print $5,$8,$14,$16,$18}'""")
            memorys = parser.filter_list(r"size[ :]+[0-9]{1,2}[ ]+GB.*")

            self.step(2, "check memory info")
            for mem_info in memorys:
                p = StrParser(mem_info)

                # 检验 memory 内存大小
                memory_size = p.get_value(f"Size: ([0-9 ]+GB)")
                memory_size = "".join(memory_size.split(" "))
                self.assertIn("memery size", e_memory_size, memory_size)

                # # 比较 memory 速率
                # m_speed = p.get_value(f"Speed: ([0-9 ]+MT/s)")
                # self.assertEqual("memery speed", m_speed, e_memory_speed)

                memory_count += 1

            # 检验memory 数量
            self.assertEqual("memory count", memory_count, e_memory_count)

        return Pass(self)


if __name__ == '__main__':
    runner.single_runner(FuncMemoryCheck)

