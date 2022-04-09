# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   FuncServerHealthLedTest.py
@Time    :   2023/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/UART测试
'''
import os
import sys

load_list = ["LuxScript"]


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

from Lib.Result import Pass, Fail
from Lib.Template import TempItem
from Lib.Runner import runner
from Lib.Error import Error
from Utils.Constant import ErrorCode


class FuncServerHealthLedTest(TempItem):

    def __init__(self):
        super().__init__()
        self.name = "server led"
        self.expect = "This is server led function check test"

        self.config = []

    def exe(self):
        # logger 日志器删除 StreamHandler
        hander = self.logger.parent.handlers[0]
        self.logger.parent.removeHandler(self.logger.parent.handlers[0])

        self.sleep(2)
        tips = self.tips_msg("请查看机头健康灯! (G/g: 健康灯Pass, R/r: 健康灯Fail)")
        self.logger.info(tips)

        print(tips)
        select_tips = self.tips_msg("请输入选择字母[G/g R/r]: ")
        self.logger.info(select_tips)
        status = input(select_tips)
        self.logger.info(f"输入结果是: {status}")

        # logger日志器添加StreamHandler
        self.logger.parent.addHandler(hander)
        if status.lower() == 'g':
            return Pass(self)

        return Fail(self, Error("机头健康灯检查失败", ErrorCode.LEDT0008))


if __name__ == '__main__':
    runner.single_runner(FuncServerHealthLedTest)
