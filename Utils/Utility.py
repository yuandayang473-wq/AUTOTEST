#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@ins-ict.com
@Software:   V2
@File    :   BmcUtility.py
@Time    :   2022/8/22
@Version :   1.0
@License :   Copyright ©ins  2022 . All Rights Reserved.
@Desc    :   bmc common function
"""
import functools
import time
import datetime
import os
import contextlib


def current_datetime(time_format='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.now().strftime(time_format)


def trans_format(time_string, from_format, to_format='%Y.%m.%d %H:%M:%S'):
    """
    @note 时间格式转化
    :param time_string:
    :param from_format:
    :param to_format:
    :return:
    """
    time_struct = time.strptime(time_string, from_format)
    times = time.strftime(to_format, time_struct)
    return times


def timestamp(time_str, from_format):
    utcTime1 = datetime.datetime.strptime(time_str, from_format)
    # 这个时间之后为正 之前为负
    utcTime2 = datetime.datetime.strptime("1970-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
    metTime = utcTime1 - utcTime2  # 两个日期的 时间差
    timeStamp = metTime.days * 24 * 3600 + metTime.seconds  # 换算成秒数
    # return int(time.mktime(time.strptime(time_str, from_format)))
    return timeStamp


def time_to_sec(time_str, from_format):
    time_ = time.strptime(time_str, from_format)
    h = time_.tm_hour
    m = time_.tm_min
    s = time_.tm_sec
    return h * 3600 + m * 60 + s


def trans_timedelta(time_str, from_format, hours=8):
    fd = datetime.datetime.strptime(time_str, from_format)
    fd = (fd + datetime.timedelta(hours=hours)).strftime(from_format)
    return fd


def read_file(file):
    data = ""
    with open(file, "r", encoding="utf-8") as f:
        while True:
            d = f.read(1024)
            if not d:
                break
            data += d
    return data


def make_dir(dir):
    # make empty dir
    if os.path.exists(dir):
        for f_name in os.listdir(dir):
            os.remove(os.path.join(dir, f_name))
    else:
        os.mkdir(dir)


class Timer:
    second = 0

    @staticmethod
    @contextlib.contextmanager
    def timer():
        start_time = time.time()
        yield
        end_time = time.time()
        Timer.second = end_time - start_time


def power(x):
    """
    x = 2 ** n, 求n 的值
    :param x:
    :return: 指数
    """
    count = 0

    while x // 2 != 0:
        x //= 2
        count += 1
    return count


def _data(data, s_column, e_column=None, separator="|", exclude=[], keyword={}, stop=False, ignore_space=True):
    """
    :param data: sensor/sdr list response data
    :param s_column: start column
    :param e_column: end column
    :return:
    """

    def get_data(r_d, c, ks):
        d = []
        temp = []
        flag = True
        for i in c:
            v = r_d[i].strip()
            match = ks.get(i, None)
            if match:
                if match.lower() in v.lower():
                    temp.append(v)
                else:
                    flag = False
            else:
                temp.append(v)
        if flag:
            d = temp
        return d

    lines = data.split("\n")
    count = 0
    column_data = []
    # for line in lines:
    for i in range(len(lines)):
        if i in exclude:
            continue
        line = lines[i]
        row_data = line.split(separator)

        # 过滤列表中的 ""
        if ignore_space:
            r_d = []
            for c in row_data:
                if c:
                    r_d.append(c)
            row_data = r_d

        if e_column is not None:
            if s_column[-1] < e_column < len(row_data):
                if len(s_column) > 1:
                    s_column.extend([i for i in range(s_column[-1], e_column + 1)])
                else:
                    s_column = [i for i in range(s_column[-1], e_column + 1)]

        res = get_data(row_data, s_column, keyword)
        if res:
            column_data.append(res)
            if stop:
                break
        count += 1

    return column_data, count


def a_column(data, column_index, separator="|", exclude=[], keyword={}, stop=False, ignore_space=True):
    column_data, count = _data(data, [column_index], separator=separator, exclude=exclude, keyword=keyword, stop=stop,
                               ignore_space=ignore_space)
    return [c[0] for c in column_data]


def multi_column(data, column_index, separator="|", exclude=[], keyword={}, stop=False, ignore_space=True):
    column_data, count = _data(data, column_index, separator=separator, exclude=exclude, keyword=keyword, stop=stop,
                               ignore_space=ignore_space)
    return column_data


def continuous_column(data, s_column, e_column, separator="|", exclude=[], keyword={}, stop=False, ignore_space=True):
    """
    :param data: sensor/sdr list response data
    :param s_column: format s_column=0,s_column=[0],s_column=[0,3]
    :param e_column:format e_column> s s_column, must be int
    :return:
    """
    s_column = [s_column] if isinstance(s_column, int) else s_column
    column_data, count = _data(data, s_column, e_column, separator=separator, exclude=exclude, keyword=keyword,
                               stop=stop, ignore_space=ignore_space)
    return column_data


def need_exec_cmd(cmd="reboot"):
    def reboot(func):
        @functools.wraps(func)
        def wrapper(self):
            setattr(self, "need_exec_cmd", cmd)
            func(self)

        return wrapper

    return reboot


if __name__ == "__main__":
    pass
