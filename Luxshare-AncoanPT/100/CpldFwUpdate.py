# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Lujuncheng
@Contact :   Juncheng.Lu@luxshare-ict.com
@Software:   TestCase
@File    :   CpldFwUpdate.py
@Time    :   2022/5/6
@Version :   1.0
@License :   Copyright ©LuxShare  2023 . All Rights Reserved.
@Desc    :   None
'''
import os
import sys
import re

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

from Lib.Result import Pass
from Lib.Template import TempItem
from Lib.Runner import runner
from Utils.Init import load_mes_info
from Utils.Constant import ErrorCode


class CpldFwUpdate(TempItem):

    @load_mes_info
    def __init__(self):
        super().__init__()
        self.name = "cpld fw update"
        self.expect = "This is cpld fw update for normal case."

        self.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
            {"file": "BmcDevice.yaml", "name": "BMC_TAIL", "key": "BMC_01"},
            {"file": "BmcDevice.yaml", "name": "BMC_HEADER", "key": "BMC_03"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "FwVersion.yaml", "name": "FwVsersion", "key": "FW-VERSION"},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "UUT.yaml", "name": "cfg", "key": self.mes_info["info"]["rk"]},
            {"folder": "Luxshare-AncoanPT/100/Config", "file": "UUT.yaml", "name": "InitPath", "key": "InitPath"},
        ]
        self.flash_flag = False

    def head_nvme_bp_cpld(self):
        self.logger.info("=======================Start head nvme fw update Test============================")
        FwVsersion = self.config["FwVsersion"]
        init_path = self.config["InitPath"]
        with self.ssh_connect(uut=self.config["BMC_HEADER"]):
            parser = self.execute_run("ipmitool alioem version")
            version = parser.get_value("Disk BackPlane[=]+\W+[a-zA-Z0-9\t ]+Version:[ ]+(\d+)")

        self.logger.info(f"current version: {version} target version: {FwVsersion['header_nvmebp']} ")

        if version !="Null" and version != FwVsersion["header_nvmebp"]:

            bmc = self.config["BMC_HEADER"]
            ip = bmc["ip_address"]
            user = bmc["username"]
            password = bmc["password"]

            headnvmebp = init_path["headnvmebp"]
            tool = headnvmebp["tool"]
            fw = headnvmebp['fw']

            parser = self.os_run.run(f"{tool} {ip} {user} {password} {fw}")
            if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                self.logger.info("head nvmebp1 flash bure fail")
                self.fail("Tail nvmebp1 flash bure fail")

        self.logger.info("========================End head nvme fw update Test=============================")


    def exe(self):
        m_config = self.config["cfg"]["JBOG"]["config"]
        tail_bmc_ip = self.config["BMC_TAIL"]["ip_address"]
        header_bmc_ip = self.config["BMC_HEADER"]["ip_address"]
        FwVsersion = self.config["FwVsersion"]
        path = self.config["InitPath"]

        current_versions = {
            'ubb1': '',
            'ubb2': '',
            'fanbp80': '',
            'fanbp40': '',
            'nvmebp1': '',
            'nvmebp2': '',
            'hib_ver': '',
            'cpuboard_ver': '',
            'cmuboard_ver': ''
        }

        self.logger.info("========================Get tail cpld version===========================")
        with self.ssh_connect(uut=self.config["BMC_TAIL"]):
            parser = self.execute_run("i2ctransfer -y 13 w2@0x20 0x00 0x05 r1", desc="ubb1 cpld version")
            current_versions['ubb1'] = parser.get_origin_data().strip()
            parser = self.execute_run("i2ctransfer -y 13 w2@0x34 0x00 0x05 r1", desc="ubb2 cpld version")
            current_versions['ubb2'] = parser.get_origin_data().strip()
            parser = self.execute_run("i2cset -y 5 0x70 2;i2ctransfer -y 5 w2@0x10 0x00 0x00 r1", desc="fanbp80 cpld version")
            current_versions['fanbp80'] = parser.get_origin_data().strip()

            if m_config == "W scaleout":
                parser = self.execute_run("i2cset -y 5 0x70 0x04;i2ctransfer -y 5 w2@0x10 0x00 0x00 r1")
                current_versions['fanbp40'] = parser.get_origin_data().strip()

            parser = self.execute_run("i2cset -y 8 0x70 1;i2ctransfer -y 8 w2@0x10 0x00 0x00 r1",desc="nvmebp1 cpld version")
            current_versions['nvmebp1'] = parser.get_origin_data().strip()

            parser = self.execute_run("i2cset -y 8 0x70 2;i2ctransfer -y 8 w2@0x10 0x00 0x00 r1",desc="nvmebp2 cpld version")
            current_versions['nvmebp2'] = parser.get_origin_data().strip()

            parser = self.execute_run("i2ctransfer -y 11 w2@0x10 0x00 0x05 r1",desc="hib cpld version")
            current_versions['hib_ver'] = re.search(r'0x\w+', parser.get_origin_data().strip(), re.I).group()

        self.logger.info("======================Get tail cpld version complete========================")
        self.logger.info("========================Get header cpld version===========================")
        with self.ssh_connect(uut=self.config["BMC_HEADER"]):
            # cpuboard
            parser = self.execute_run("ipmitool alioem version | grep -i cpld1 | head -n1", desc="head cpld cpu board version")
            current_versions['cpuboard_ver'] = re.search(r'\d+.\d+', parser.get_origin_data()).group()
            # cmu
            parser = self.execute_run("ipmitool alioem version | grep -iw -A1 cmu | tail -n1", desc=" head cpld cmuboard version")
            current_versions['cmuboard_ver'] = re.search(r'\d+.\d+', parser.get_origin_data()).group()
        self.logger.info(current_versions)
        self.logger.info("=======================Get header cpld version complete=============================")

        self.os_run.run(f"ipmitool -I lanplus -H {tail_bmc_ip} -U admin -P admin power off")

        self.sleep(20)
        # ubb1
        self.logger.info("========================Start UBB1 fw update Test===========================")
        self.logger.info(
            f"Current ubb1 cpld version is: {current_versions['ubb1']}, target version is {FwVsersion.get('ubb1')}")
        if current_versions['ubb1'] != FwVsersion.get("ubb1"):
            flag = "update"
            ubb1 = path["ubb1"]
            tool = ubb1["tool"]
            fw = ubb1['40FCB']['fw']
            self.flash_flag = True

            parser = self.os_run.run(f"{tool} {tail_bmc_ip} admin admin {fw}")
            if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                self.logger.info("Tail ubb1 flash bure fail")
                self.fail("Tail ubb1 flash bure fail")
        else:
            flag = "un update"
        self.logger.info(f"current version: {current_versions['ubb1']} target version: {FwVsersion.get('ubb1')} update status: {flag}")
        self.logger.info("========================End UBB1 fw update Test=============================")

        # UBB2
        self.logger.info("======================Start UBB2 fw update Test==========================")
        self.logger.info(
            f"Current ubb2 cpld version is: {current_versions['ubb2']}, target version is {FwVsersion.get('ubb2')}")
        if current_versions['ubb2'] != FwVsersion.get("ubb2"):
            flag = "update"
            self.flash_flag = True
            ubb2 = path["ubb2"]
            tool = ubb2["tool"]
            fw = ubb2['40FCB']['fw']

            parser = self.os_run.run(f"{tool} {tail_bmc_ip} admin admin {fw}")
            if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                self.logger.info("Tail ubb2 flash bure fail")
                self.fail("Tail ubb2 flash bure fail")
        else:
            flag = "un update"
        self.logger.info(f"current version: {current_versions['ubb2']} target version: {FwVsersion.get('ubb2')} update status: {flag}")
        self.logger.info("========================End UBB2 fw update Test=============================")

        # 80 fan board
        self.logger.info("======================Start 80 fan borad fw update Test==========================")
        self.logger.info(
            f"Current ubb2 cpld version is: {current_versions['fanbp80']}, target version is {FwVsersion.get('fanbp80')}")
        if current_versions['fanbp80'] != FwVsersion.get("fanbp80"):
            self.logger.info(current_versions['fanbp80'] != FwVsersion.get("fanbp80"))
            flag = "update"
            self.flash_flag = True

            fanboard = path["fanboard"]
            tool = fanboard["tool"]
            fw = fanboard['80FCB']['fw']

            parser = self.os_run.run(f"{tool} {tail_bmc_ip} admin admin {fw}")
            if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                self.logger.info("Tail 80 fan board flash bure fail")
                self.fail("Tail 80 fan board flash bure fail")
        else:
            flag = "un update"
        self.logger.info(f"current version: {current_versions['fanbp80']} target version: {FwVsersion.get('fanbp80')} update status: {flag}")
        self.logger.info("========================End 80 fan board fw update Test=============================")

        # 40 fan board
        if m_config == "W scaleout":
            self.logger.info("=======================Start 40 fan borad fw update Test============================")
            if current_versions['fanbp40'] != FwVsersion.get("fanbp40"):
                flag = "update"
                self.flash_flag = True
                fanboard = path["fanboard"]
                tool = fanboard["tool"]
                fw = fanboard['40FCB']['fw']

                parser = self.os_run.run(f"{tool} {tail_bmc_ip} admin admin {fw}")
                if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                    self.logger.info("Tail 40 fan board bure fail")
                    self.fail("Tail 40 fan board flash bure fail")
            else:
                flag = "un update"
            self.logger.info(f"current version: {current_versions['fanbp40']} target version: {FwVsersion.get('fanbp40')} update status: {flag}")
            self.logger.info("========================End 40 fan board fw update Test=============================")

        # check nmve bp1 fw verion
        self.logger.info("=======================Start nvme fw update Test============================")
        self.logger.info(
            f"Current ubb2 cpld version is: {current_versions['nvmebp1']}, target version is {FwVsersion.get('nvmebp1')}")
        if current_versions['nvmebp1'] != FwVsersion.get("nvmebp1") or current_versions['nvmebp2'] != FwVsersion.get("nvmebp2"):
            self.flash_flag = True

            nvmebp = path["nvmebp"]
            tool = nvmebp["tool"]
            bp1_fw = nvmebp['BP1']['fw']
            bp2_fw= nvmebp['BP1']['fw']

            parser = self.os_run.run(f"{tool} {tail_bmc_ip} admin admin {bp1_fw}")
            if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                self.logger.info("Tail nvmebp1 flash bure fail")
                self.fail("Tail nvmebp1 flash bure fail")

            self.logger.info(f"current version: {current_versions['nvmebp1']} target version: {FwVsersion.get('nvmebp1')} update status: update")
            self.logger.info("========================End nvme bp1 fw update Test=============================")

            parser = self.os_run.run(f"{tool} {tail_bmc_ip} admin admin {bp2_fw}")
            if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                self.logger.info("Tail nvmebp2 flash bure fail")
                self.fail("Tail nvmebp2 flash bure fail")
            self.logger.info(f"current version: {current_versions['nvmebp2']} target version: {FwVsersion.get('nvmebp2')} update status: update")
            self.logger.info("========================End nvme bp2 fw update Test=============================")
        else:
            self.logger.info(f"current version: {current_versions['nvmebp1']} target version: {FwVsersion.get('nvmebp1')} update status: un update")
            self.logger.info(f"current version: {current_versions['nvmebp2']} target version: {FwVsersion.get('nvmebp2')} update status: un update")

        self.logger.info(f"current version: {current_versions['nvmebp2']} target version: {FwVsersion.get('nvmebp2')} update status: {flag}")
        self.logger.info("========================End nvme bp2 fw update Test=============================")

        self.head_nvme_bp_cpld()

        self.logger.info("======================Start hib fw update Test==========================")

        # check HIB fw verion
        self.os_run.run("rm -rf /root/BMCLog", i_exit_code=True)
        self.logger.info(
            f"Current ubb2 cpld version is: {current_versions['hib_ver']}, target version is {FwVsersion.get('hib_ver')}")
        if current_versions['hib_ver'] != FwVsersion.get("hib_ver"):
            flag = "update"

            nvmebp = path["hib"]
            tool = nvmebp["tool"]
            fw = nvmebp['fw']

            self.flash_flag = True
            self.os_run.run(f"{tool} {tail_bmc_ip} admin admin {fw}",timeout=60 * 5, i_timeout_err=True, retry_expt=1)

        else:
            flag = "un update"
        self.logger.info(f"current version: {current_versions['hib_ver']} target version: {FwVsersion.get('hib_ver')} update status: {flag}")
        self.logger.info("========================End hib fw update Test=============================")

        # upadte header cpld fw version

        self.logger.info("======================Start cpuboard fw update Test==========================")
        if current_versions['cpuboard_ver'] != FwVsersion.get("cpuboard_ver"):
            flag = "update"
            headercpld = path["headercpld"]
            tool = headercpld["tool"]
            fw = headercpld["CPUboard"]['fw']
            self.flash_flag = True

            parser = self.os_run.run(f"{tool} {header_bmc_ip} taobao 9ijn0okm {fw}")
            if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                self.logger.info("Tail cpubord flash bure fail")
                self.fail("Tail cpubord flash bure fail")
        else:
            flag = "un update"
        self.logger.info(f"current version: {current_versions['cpuboard_ver']} target version: {FwVsersion.get('cpuboard_ver')} update status: {flag}")
        self.logger.info("========================End cpuboard fw update Test=============================")
        self.sleep(3)
        self.logger.info("======================Start cmu fw update Test==========================")

        if current_versions['cmuboard_ver'] != FwVsersion.get("cmuboard_ver"):
            flag = "update"

            headercpld = path["headercpld"]
            tool = headercpld["tool"]
            fw = headercpld["CMU"]['fw']

            self.flash_flag = True
            parser = self.os_run.run(f"{tool} {header_bmc_ip} taobao 9ijn0okm {fw}")
            if not re.search(r'Flash\s*Complete', parser.get_origin_data(), re.I):
                self.logger.info("Tail cmu flash bure fail")
                self.fail("Tail cmu flash bure fail")
        else:
            flag = "un update"
        self.logger.info(f"current version: {current_versions['cmuboard_ver']} target version: {FwVsersion.get('cmuboard_ver')} update status: {flag}")
        self.logger.info("========================End cmu fw update Test=============================")

        self.platform.put_platform_data(self.config["BMC_TAIL"])


if __name__ == '__main__':
    runner.single_runner(CpldFwUpdate)

