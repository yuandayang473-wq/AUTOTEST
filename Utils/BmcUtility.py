#! /usr/bin/python3
# coding=utf-8
"""
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   V2
@File    :   BmcUtility.py
@Time    :   2022/8/22
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   bmc common function
"""
from Utils.DataBuffer import DataRawParse
from Lib.Template import TempItem
from Lib.Runner import runner
from Cmd.Cmd import Chassis


class BiosTempItem(TempItem):

    def setup(self):
        with self.ssh_connect():
            parser = self.execute_run(Chassis.power_status)


def _name(data):
    """
    :param data: sensor/sdr list response data
    :param s_column: start column
    :param e_column: end column
    :return:
    """
    lines = data.split("\n")
    count = 0
    names = []
    for line in lines:
        names.append(line.split("|")[0].strip())
        count += 1

    return names, count


def sdr_names(data):
    return _name(data)


def sensor_names(data):
    return _name(data)


def record_count(record):
    return len(record.split("\n"))


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


def continuous_column(data, s_column, e_column, separator="|", exclude=[], keyword={}, stop=False,
                      ignore_space=True):
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


class _DecryptRaw:

    @classmethod
    def pick(cls, parser):
        if not isinstance(parser, DataRawParse):
            raise TypeError("parser must DataRawParse")


class DecryptOemCmd(_DecryptRaw):
    class GetVersionInfo:
        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        @property
        def bios_version(self):
            origin_list = self.parser.get_data_list()
            version = ""
            for i in origin_list[1:]:
                version += chr(int(i, 16))
            return version

        @property
        def cpld_version(self):
            origin_list = self.parser.get_data_list()
            version = ""
            for i in origin_list[-2:]:
                version += chr(int(i, 16))
            return version

    class GetLogInfo:
        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        @property
        def total(self):
            total = self.parser.get_unit16(1)
            return total

        @property
        def last_record_id(self):
            last_record_id = self.parser.get_unit16(3)
            return last_record_id

    class GetDeviceStatus:

        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        @property
        def system_health_status(self):
            status_dict = {
                0: "ok", 1: "minor", 2: "major", 3: 'critical'
            }
            status = self.parser.get_bit(offset=0, bit_offset=0, length=3)
            return status_dict[status]

    class GetDeviceInformation:
        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        @property
        def version(self):
            origin_list = self.parser.get_data_list()
            version = ""
            for i in origin_list:
                version += chr(int(i, 16))
            return version

        @property
        def device_manufacturer(self):
            origin_list = self.parser.get_data_list()
            index = origin_list.index("0f")
            d_m = ""
            for i in origin_list[:index]:
                d_m += chr(int(i, 16))
            return d_m.strip()

        @property
        def device_part_number(self):
            origin_list = self.parser.get_data_list()
            index1 = origin_list.index("0f")
            index2 = origin_list.index("08")
            d_p_n = ""
            for i in origin_list[index1 + 1:index2]:
                d_p_n += chr(int(i, 16))
            return d_p_n.strip()

        @property
        def fw_version(self):
            origin_list = self.parser.get_data_list()
            index1 = origin_list.index("08")
            index2 = origin_list.index("02")
            f_w = ""
            for i in origin_list[index1 + 1:index2]:
                f_w += chr(int(i, 16))
            return f_w.strip()

        @property
        def hw_version(self):
            origin_list = self.parser.get_data_list()
            index = origin_list.index("02")
            h_w = ""
            for i in origin_list[index + 1:]:
                h_w += chr(int(i, 16))
            return h_w.strip()

    class GetBiosConfigurationValue:
        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        @property
        def data_length(self):
            return self.parser.get_unit8(0)

        def value(self, index):
            origin_list = self.parser.get_data_list()
            return origin_list[index + 1]

    class GetManagementInformation:

        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        @property
        def version(self):
            return self.parser.get_unit8(0)

    class GetBios80PortInfo:
        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        def info(self):
            origin_list = self.parser.get_data_list()
            info = ""
            for i in origin_list[1:]:
                info += chr(int(i, 16))
            return info

    class GetLogEntry:
        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        @property
        def record_id(self):
            int_id = self.parser.get_unit16(2)
            origin_list = self.parser.get_data_list()
            hex_id = (origin_list[2], origin_list[3])
            return int_id, hex_id

        @property
        def next_record_id(self):
            int_id = self.parser.get_unit16(0)
            origin_list = self.parser.get_data_list()
            hex_id = ("0x%s" % origin_list[0], "0x%s" % origin_list[1])
            return int_id, hex_id

        @property
        def timestamp(self):
            origin_list = self.parser.get_data_list()
            tts = origin_list[4:8]
            tts.reverse()
            return int("".join(tts), 16)

        @property
        def eventcode(self):
            origin_list = self.parser.get_data_list()
            eventcodes = origin_list[8:12]
            eventcodes.reverse()
            return "0x%s" % "".join(eventcodes)

        @property
        def level(self):
            status_dict = {
                0: "ok", 1: "minor", 2: "major", 3: 'critical'
            }
            level_status = self.parser.get_unit8(12)
            return status_dict[level_status]

        @property
        def warning_info(self):
            origin_list = self.parser.get_data_list()
            warnings = origin_list[16:]
            infos = [chr(int(c, 16)) for c in warnings]
            return "".join(infos)

    class GetSMBIOSInformation:

        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        @property
        def cpu_present(self):
            return self.parser.get_unit8(0)

        @property
        def cpu_enable(self):
            # d = {
            #     0: 'disabled',
            #     1: 'enabled'
            # }
            # int_enable = self.parser.get_unit8(1)
            # return d[int_enable]
            return self.parser.get_unit8(1)

        @property
        def cpu_step(self):
            return self.parser.get_unit8(2)

        @property
        def cpu_process_name(self):
            origin_list = self.parser.get_data_list()
            p_name = ""
            for i in origin_list[3:51]:
                if i == '00':
                    continue
                p_name += chr(int(i, 16))
            return p_name

        @property
        def cpu_id(self):
            origin_list = self.parser.get_data_list()
            _id = " ".join([d.upper() for d in origin_list[51:59]])
            return _id

        @property
        def cpu_microcode(self):
            origin_list = self.parser.get_data_list()
            _id = " ".join(origin_list[59:63])
            return _id

        @property
        def cpu_maxspeed(self):
            # origin_list = self.parser.get_data_list()
            speed = self.parser.get_unit16(63)
            # speed = " ".join(origin_list[63:65])
            return speed

        @property
        def cpu_core(self):
            # origin_list = self.parser.get_data_list()
            # core = " ".join(origin_list[65:67])
            core = self.parser.get_unit16(65)
            return core

        @property
        def cpu_usercore(self):
            # origin_list = self.parser.get_data_list()
            # usercore = " ".join(origin_list[67:69])
            usercore = self.parser.get_unit16(67)
            return usercore

        @property
        def cpu_l1_cache(self):
            # origin_list = self.parser.get_data_list()
            # l1_cache = " ".join(origin_list[69:71])
            l1_cache = self.parser.get_unit16(71)
            return l1_cache

        @property
        def cpu_l2_cache(self):
            # origin_list = self.parser.get_data_list()
            # l2_cache = " ".join(origin_list[71:73])
            l2_cache = self.parser.get_unit16(73)
            return l2_cache

        @property
        def cpu_l3_cache(self):
            # origin_list = self.parser.get_data_list()
            # l3_cache = " ".join(origin_list[73:75])
            l3_cache = self.parser.get_unit16(75)
            return l3_cache

        @property
        def cpu_tdp(self):
            origin_list = self.parser.get_data_list()
            tdp = " ".join(origin_list[75:77])
            return tdp

        @property
        def mem_present(self):
            return self.parser.get_unit8(0)

        @property
        def mem_enable(self):
            # d = {
            #     0: 'disabled',
            #     1: 'enabled'
            # }
            # int_enable = self.parser.get_unit8(1)
            # return d[int_enable]
            return self.parser.get_unit8(1)

        @property
        def mem_location(self):
            return self.parser.get_unit8(2)

        @property
        def mem_manufacture(self):
            origin_list = self.parser.get_data_list()
            p_name = ""
            for i in origin_list[3:13]:
                if i == '00':
                    continue
                p_name += chr(int(i, 16))
            return p_name

        @property
        def mem_max_speed(self):
            speed = self.parser.get_unit16(13)
            return speed

        @property
        def mem_current_speed(self):
            speed = self.parser.get_unit16(15)
            return speed

        @property
        def mem_type(self):
            speed = self.parser.get_unit8(17)
            return speed

        @property
        def mem_typedetail(self):
            speed = self.parser.get_unit16(18)
            return speed

        @property
        def mem_rank(self):
            speed = self.parser.get_unit8(20)
            return speed

        @property
        def mem_data_width(self):
            speed = self.parser.get_unit16(21)
            return speed

        @property
        def mem_configure_voltage(self):
            speed = self.parser.get_unit16(23)
            return speed / 1000

        @property
        def mem_physical_size(self):
            speed = self.parser.get_unit16(25)
            return speed

        @property
        def mem_sn(self):
            origin_list = self.parser.get_data_list()
            p_name = ""
            for i in origin_list[27:37]:
                if i == '00':
                    continue
                p_name += chr(int(i, 16))
            return p_name

        @property
        def mem_pn(self):
            origin_list = self.parser.get_data_list()
            p_name = ""
            for i in origin_list[37:69]:
                if i == '00':
                    continue
                p_name += chr(int(i, 16))
            return p_name.strip()

        @property
        def mem_sn_ext(self):
            origin_list = self.parser.get_data_list()
            p_name = ""
            for i in origin_list[69:101]:
                if i == '00':
                    continue
                p_name += chr(int(i, 16))
            return p_name.strip()

        @property
        def pcie_present(self):
            return self.parser.get_unit8(0)

        @property
        def pcie_enable(self):
            # d = {
            #     0: 'disabled',
            #     1: 'enabled'
            # }
            # int_enable = self.parser.get_unit8(1)
            # return d[int_enable]
            return self.parser.get_unit8(1)

        @property
        def pcie_present_type(self):
            # d = {
            #             #     0: 'OnBoard',
            #             #     1: 'OffBoard'
            #             # }
            #             # int_enable = self.parser.get_unit8(2)
            #             # return d[int_enable]
            return self.parser.get_unit8(2)

        @property
        def pcie_bus_number(self):
            origin_list = self.parser.get_data_list()
            return '0x' + origin_list[3]

        @property
        def pcie_device_number(self):
            origin_list = self.parser.get_data_list()
            return '0x' + origin_list[4]

        @property
        def pcie_function_number(self):
            origin_list = self.parser.get_data_list()
            return '0x' + origin_list[5]

        @property
        def pcie_max_link_width(self):
            return self.parser.get_unit8(6)

        @property
        def pcie_max_link_speed(self):
            return self.parser.get_unit8(7)

        @property
        def pcie_current_link_width(self):
            return self.parser.get_unit8(8)

        @property
        def pcie_current_link_speed(self):
            return self.parser.get_unit8(9)

        @property
        def pcie_type(self):
            return self.parser.get_unit8(10)

        @property
        def pcie_pcie_slot(self):
            return self.parser.get_unit8(11)

        @property
        def pcie_riser_type(self):
            return self.parser.get_unit8(12)

        @property
        def pcie_pcielocationonriser(self):
            return self.parser.get_unit8(13)

        @property
        def pcie_designation(self):
            origin_list = self.parser.get_data_list()
            p_name = ""
            for i in origin_list[13:45]:
                if i == '00':
                    continue
                p_name += chr(int(i, 16))
            return p_name.strip()

    class GetSensorValue:
        def __init__(self, parser) -> None:
            DecryptOemCmd.pick(parser)
            self.parser = parser

        def _int_value(self):
            return self.parser.get_unit16(0)

        def _float_value(self):
            return self.parser.get_unit8(2) / 256

        @property
        def fan_speed_rpm_int(self):
            return self._int_value()

        @property
        def fan_speed_rpm_float(self):
            return self._float_value()

        @property
        def psu_input_power(self):
            return self._int_value() + round(self._float_value(), 2)


class Dmidecode:

    def __init__(self, parser):
        self.parser = parser


class CpuDmidecode(Dmidecode):

    def __init__(self, parser):
        super().__init__(parser)

    @property
    def version(self):
        return self.parser.get_value("version: ([\w-]+)")

    @property
    def cpu_id(self):
        return self.parser.get_value(r"ID: ([A-Za-z0-9 ]+)")

    @property
    def max_speed(self):
        return int(self.parser.get_value(r"Max Speed: (\d+) MHz"))

    @property
    def core_count(self):
        return int(self.parser.get_value(r"Core Count: (\d+)"))

    @property
    def core_enable(self):
        return int(self.parser.get_value(r"Core Enabled: (\d+)"))


class MemoryDmidecode(Dmidecode):

    def __init__(self, parser):
        super().__init__(parser)

    @property
    def manufacturer(self):
        return self.parser.get_value(r"Manufacturer: (\w+)")

    @property
    def max_speed(self):
        return int(self.parser.get_value(r"Speed: (\d+) MT/s"))

    @property
    def configured_memory_speed(self):
        return int(self.parser.get_value(r"Configured Memory Speed: (\d+) MT/s"))

    @property
    def configured_voltage(self):
        return float(self.parser.get_value(r"Configured Voltage: ([\d\.]+) V"))

    @property
    def rank(self):
        return int(self.parser.get_value(r"Rank: (\d+)"))

    @property
    def data_width(self):
        return int(self.parser.get_value(r"Data Width: (\d+) bits"))

    @property
    def size(self):
        return int(self.parser.get_value(r"Size: (\d+) GB"))

    @property
    def part_number(self):
        return self.parser.get_value(r"Part Number: ([\w]+)")

    @property
    def serial_number(self):
        return self.parser.get_value(r"Serial Number: ([\w]+)")


class DecryptAliOem:
    def __init__(self, parser):
        self.parser = parser


class GetSMBiosInformation(DecryptAliOem):

    def __init__(self, parser):
        super().__init__(parser)

    @property
    def cpu_present(self):
        return int(self.parser.get_value(r"Present: (\d+)"))

    @property
    def cpu_enbale(self):
        return int(self.parser.get_value(r"enable: (\d+)"))

    @property
    def cpu_step(self):
        return int(self.parser.get_value(r"step: (\d+)"))

    @property
    def cpu_process_name(self):
        return self.parser.get_value(r"ProcessName: (a{3})")

    @property
    def mem_present(self):
        return int(self.parser.get_value(r"Present: (\d+)"))

    @property
    def mem_enable(self):
        return int(self.parser.get_value(r"enable: (\d+)"))

    @property
    def mem_location(self):
        return int(self.parser.get_value(r"Location: (0x08)"), 16)

    @property
    def mem_manufacture(self):
        return self.parser.get_value(r"Manufacture: (a{3})")

    @property
    def pcie_present(self):
        return int(self.parser.get_value(r"Present: (\d+)"))

    @property
    def pcie_enable(self):
        return int(self.parser.get_value(r"Enable: (\d+)"))

    @property
    def pcie_present_type(self):
        return int(self.parser.get_value(r"PresentType: (\d+)"))

    @property
    def pcie_bus_number(self):
        return self.parser.get_value(r"BusNumber: (0x[0-9]+)")

    @property
    def pcie_device_number(self):
        return self.parser.get_value(r"DeviceNumber: (0x[0-9]+)")

    @property
    def pcie_function_number(self):
        return self.parser.get_value(r"FunctionNumber: (0x[0-9]+)")

    @property
    def pcie_max_link_width(self):
        return int(self.parser.get_value(r"MaxLinkWidth: (\d+)"))

    @property
    def pcie_max_link_speed(self):
        return int(self.parser.get_value(r"MaxLinkSpeed: (\d+)"))

    @property
    def pcie_current_link_width(self):
        return int(self.parser.get_value(r"CurrentlinkWidth: (\d+)"))

    @property
    def pcie_current_link_speed(self):
        return int(self.parser.get_value(r"CurrentLinkSpeed: (\d+)"))

    @property
    def pcie_type(self):
        return int(self.parser.get_value(r"^Type: (\d+)"))

    @property
    def pcie_slot(self):
        return int(self.parser.get_value(r"PCIEslot: (\d+)"))

    @property
    def pcie_riser_type(self):
        return int(self.parser.get_value(r"RiserType: (\d+)"))

    @property
    def pcie_location_on_riser(self):
        return int(self.parser.get_value(r"PcieLocationOnRiser: (\d+)"))

    @property
    def pcie_designation(self):
        return self.parser.get_value(r"Designation: ([\w_]+)")


if __name__ == "__main__":
    pass
