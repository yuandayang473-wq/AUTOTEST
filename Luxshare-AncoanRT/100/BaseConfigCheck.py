# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   陈进文
@Contact :   jinwen.chen@luxshare-ict.com
@Software:   TestCase
@File    :   BaseConfigCheck.py
@Time    :   2023/6/19
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   功能检查/CPU测试 （机头）
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

from Lib.Template import TempItem
from Lib.DataBuffer import StrParser
from Utils.Utility import multi_column
from Utils.Init import load_mes_info
from Utils.Constant import ErrorCode
from Lib.Runner import runner


class BaseConfigCheck(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "PowerCycle"
        self.expect = "This is PowerCycle for normal case."

        self.config = [
            {"file": "BmcDevice.yaml", "name": "JBOG_BMC", "key": "BMC_01"},
            {"folder": "Luxshare-AncoanRT/100/Config", "file": "UUT.yaml", "name": "cfg","key": self.mes_info["info"]["rk"]},
            {"folder": "Luxshare-AncoanRT/100/Config", "file": "UUT.yaml", "name": "oam_conf", "key": "OAM"},
            {"folder": "Luxshare-AncoanRT/100/Config", "file": "UUT.yaml", "name": "fw", "key": "tools/ancoan/fw"},
        ]

    def cpu(self):
        server = self.config["cfg"]["SERVER"]
        e_model_name = server["cpu_type"]
        e_socket_count = server["cpu_count"]

        with self.action("cpu"):
            parser = self.os_run.run("lscpu")

            # cpu 个数
            socket_count = int(parser.get_value(r"Socket\(s\)[ :]+(\d+)"))
            self.assertEqual(ErrorCode.CUTCH001, f"cpu socket count", socket_count, e_socket_count)

            # cpu 型号
            model_name = parser.get_value(r"Model name[ :]+([\S ]+)")
            self.assertIn(ErrorCode.CUTCH002, f"cpu model name", e_model_name, model_name)

    def memory(self):
        server = self.config["cfg"]["SERVER"]
        e_memory_count = server["mem_count"]
        e_memory_size = server["mem_size"]
        # e_memory_speed = mem_config["Speed"]
        memory_count = 0

        with self.action("memory"):
            # self.step(1, "get memory info")
            parser = self.os_run.run(
                r"""dmidecode -t 17 |awk 'BEGIN{RS="Memory Device\n";FS="\n"}{print $5,$8,$14,$16,$18}'""")
            memorys = parser.filter_list(r"size[ :]+[0-9]{1,2}[ ]+GB.*")

            # self.step(2, "check memory info")
            for mem_info in memorys:
                p = StrParser(mem_info)

                # 检验 memory 内存大小
                memory_size = p.get_value(f"Size: ([0-9 ]+GB)")
                memory_size = "".join(memory_size.split(" "))
                self.assertIn(ErrorCode.MFTCH005, "memery size", e_memory_size, memory_size)

                # # 比较 memory 速率
                # m_speed = p.get_value(f"Speed: ([0-9 ]+MT/s)")
                # self.assertEqual("memery speed", m_speed, e_memory_speed)

                memory_count += 1

            # 检验memory 数量
            self.assertEqual(ErrorCode.MFTCH001, "memory count", memory_count, e_memory_count)

    def nvme(self):
        jbog_cfg = self.config["cfg"]["JBOG"]
        server_cfg = self.config['cfg']["SERVER"]
        tail_nvme_size = jbog_cfg["nvme_size"]
        tail_nvme_count = jbog_cfg["nvme_count"]
        head_nvme_size = server_cfg.get("nvme_size", "NA")
        head_nvme_count = server_cfg.get("nvme_count", 0)

        if tail_nvme_count == "NA":
            tail_nvme_count = 0

        if head_nvme_count == "NA":
            head_nvme_count = 0
        count = 0

        if tail_nvme_size == "NA" and head_nvme_size == "NA":
            return

        self.step(1, "get nvme info")
        parser = self.os_run.run(f"{self.config['fw']['nvme_tool']} list")
        nvmes = parser.filter_list(r"(/dev/nvme.*)")
        for nvme in nvmes:
            p1 = StrParser(nvme)
            l = p1.split(r"[ ]+")
            cur_nvme_size = l[6]
            cur_nvme_unit = l[7]

            if cur_nvme_size in tail_nvme_size:
                self.assertIn(ErrorCode.HDTCH004, f"{l[0]} size", tail_nvme_size, cur_nvme_size + cur_nvme_unit)
            elif cur_nvme_size in head_nvme_size:
                self.assertIn(ErrorCode.HDTCH004, f"{l[0]} size", head_nvme_size, cur_nvme_size + cur_nvme_unit)
            count += 1

        self.assertEqual(ErrorCode.HDTCH001, "nvme count", count, tail_nvme_count + head_nvme_count)

    def ssd(self):
        server = self.config["cfg"]["SERVER"]
        e_m2_count = server["m2_count"]
        e_m2_size = server["m2_size"]
        e_m2_type = server["m2_type"]
        c = 0
        if e_m2_size == "NA":
            return None

        with self.action("ssd"):
            # self.step(1, "get m.2 info")
            parser = self.os_run.run("lsblk | grep sd", i_exit_code=True, retry_expt=1)
            # self.step(2, "check m.2 info")

            if parser.get_origin_data() != "Null":
                m2s = multi_column(parser.get_origin_data(), column_index=[0, 3, 5], separator=" ")

                for m in m2s:
                    m2_name = m[0]
                    m2_type = m[2]
                    if m2_type == 'disk':
                        m2_size = float(m[1][:-1])
                        val = round(float(e_m2_size[:-1]) - m2_size, 1)
                        self.assertLess(ErrorCode.HDTCH004, f"m2 {m2_name} size difference value", val, 50)
                        c += 1

                self.assertEqual(ErrorCode.HDTCH001,"m2 count", c, e_m2_count)

            disk_type_cmd = f"lsscsi | grep -i '/dev/sd'"
            parser = self.os_run(disk_type_cmd)
            lines = parser.split("\n")
            m2_data = []
            for line in lines:
                if line:
                    line_list = StrParser(line).split(r" +")
                    line_list = [l for l in line_list if l]
                    m2_data.append((line_list[-3], line_list[-1]))

            for m2_type, m2_name in m2_data:
                self.assertIn(ErrorCode.HDTCH005,f"{m2_name}", m2_type, e_m2_type)

    def head_psu(self):
        server = self.config["cfg"]["SERVER"]
        # 获取机头的psu

        with self.action("head psu"):
            parser = self.os_run.run("ipmitool sdr elist | egrep -i 'PS1_Status|PS2_Status'")
            psus = multi_column(parser.get_origin_data(), column_index=[0, 4])
            self.assertEqual(ErrorCode.PSUTCH03, "server psu count", len(psus), server["psu_count"])
            for p_name, status in psus:
                self.assertEqual(ErrorCode.PSUTCH01, f"{p_name} status", status.lower(), "presence detected")

    def tail_psu(self):
        # 获取机尾的psu

        with self.ssh_connect(uut=self.config["JBOG_BMC"]):
            JBOG = self.config["cfg"]["JBOG"]
            parser = self.execute_run("ipmitool sdr elist | egrep -i 'PS[1-6]_Status'")
            psus = multi_column(parser.get_origin_data(), column_index=[0, 4])

            with self.action("tail psu"):
                self.assertEqual(ErrorCode.PSUTCH03, "JBOG psu count", len(psus), JBOG["psu_count"])
                for p_name, status in psus:
                    self.assertEqual(ErrorCode.PSUTCH01, f"{p_name} status", status.lower(), "presence detected")

    def gpu(self):
        oam_config = self.config["oam_conf"]
        with self.action("gpu"):
            for n in oam_config["Num"]:
                parser = self.os_run.run(f"ppudbg --device {n}")

                HBM_FS = parser.filter_list(r"(HBM[0-9]{1}-[0-9]+MHZ)")
                for h in HBM_FS:
                    h_l = h.split("-")
                    self.assertEqual(ErrorCode.FFFFFFFF, f"oam device {n} {h_l[0]} HBM Frequency", h_l[1], oam_config['HBM_Frequency'])

    def exe(self):
        self.cpu()
        self.memory()
        self.nvme()
        self.ssd()
        self.gpu()
        self.head_psu()
        self.tail_psu()


if __name__ == '__main__':
    runner.single_runner(BaseConfigCheck)
