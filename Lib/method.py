import json
import os
import re
import time
import traceback
from collections import defaultdict, namedtuple

import paramiko
import yaml

from Lib.Constant import *
from Lib.Error import SSHSessionError
from Lib.Utility import singleton
from Lib.base import Base
from Lib.logger import Logger

BASE = Base()
LOGGER = Logger()

@singleton
class Method:
    def get_bdf(self):
        """
        查找所有SW上usp,mep,dma,ntb,ep及dsp信息
        :return {'0000': [{'usp': '0000:06:00.0', 'eps': [{'dsp': '0000:07:00.0', 'ep': '0000:08:00.0', 'driver': 'nvme', 'name': 'EP_SSD_INTEL900P'}], 'mep': {'dsp': '0000:07:1c.0', 'ep': '0000:0e:00.0', 'driver': 'nvme', 'name': 'NA'}, 'dma': [{'dsp': '0000:07:1d.0', 'ep': '0000:0f:00.0', 'driver': '', 'name': 'NA'}, {'dsp': '0000:07:1e.0', 'ep': '0000:10:00.0', 'driver': '', 'name': 'NA'}], 'ntb': {}}]})
        """
        # 读取vendor.yml
        vendor_file = os.path.abspath(os.path.join(os.path.abspath(__file__), "../")) + "/vendor.yml"
        with open(vendor_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            sw_vd = data["SW_VD"]
            mep_vd = data["EP_SWITCH_SUDU_MEP_SUB"]
            mep_dsp_vd = data["DSP_MEP_VD"]
            dma_vd = data["EP_SWITCH_SUDU_DMA_SUB"]
            dma_dsp_vd = data["DSP_DMA_VD"]  # 列表
            ntb_vd = data["EP_SWITCH_SUDU_NTB_SUB"]
            ntb_dsp_vd = data["DSP_NTB_VD"]
            eps = data["EPS"]

        # 根据vendor id找到所有属于数渡sw的设备以及bridge
        sudu_sw = BASE.execute_run("lspci -Dd 205e:", i_record_cmd=True).get_origin_data()
        assert sudu_sw, "Not find any switch in system!"
        # 按照domain进行分类
        dict_all = defaultdict(list)
        for line in sudu_sw.splitlines():
            domain = line[:4]
            dict_all[domain].append(line)
        for key, value in dict_all.items():
            sudu_sw = value
            # 判断是否为合成模式
            sw_bdf = [i[0:12] for i in sudu_sw]
            usp = []
            sw = []
            for index, bdf in enumerate(sw_bdf):
                BASE.execute_run(f"lspci -vs {bdf} |grep 'Upstream Port'", i_exit_code=True, i_record_cmd=True)
                check_usp = BASE.ssh.get_exit_code()
                if check_usp == 0:
                    usp.append({"bdf": bdf, "index": index})
            if len(usp) > 1:
                for i in range(len(usp)):
                    if i == len(usp) - 1:
                        sw_tmp = sw_bdf[usp[i]['index']:]  # 拆分switch
                    else:
                        sw_tmp = sw_bdf[usp[i]['index']:usp[i + 1]['index']]  # 拆分switch
                    sw.append(sw_tmp)
            else:
                sw.append(sw_bdf)

            # 只考虑基础和合成模式，即最多只有2个switch情况，其它多switch情况暂不考虑
            # 判断哪个switch有mep，即sw0
            mep_list = BASE.execute_run(f'lspci -vvv | grep -B 10 -E "{mep_vd}|SDTECH Device 2006" | grep "^[0-9a-f]"', i_record_cmd=True).get_origin_data().split("\n")
            mep_ep_list = [key + ":"  + mep_ep[0:7] for mep_ep in mep_list]
            # sw_bdf = [{'usp': xxx,
            # 'eps': [{'dsp': xxx,'ep': xxx,'driver': xxx,'name': xxx},{}...],
            # 'mep': {'dsp': xxx, 'ep': xxx, 'driver': xxx},
            # 'dma': [{'dsp': xxx, 'ep': xxx, 'driver': xxx},{}...],
            # 'ntb': {'dsp': xxx, 'ep': xxx, 'driver': xxx}, {}]
            all_sudu_sw = defaultdict(list)
            dma_list = BASE.execute_run(f'lspci -vvv | grep -B 10 -E "{dma_vd}|SDTECH Device 2005" | grep "^[0-9a-f]"',
                             i_exit_code=True, i_record_cmd=True).get_origin_data().split("\n")
            dma_ep_list = [key + ":"  + dma_ep[0:7] for dma_ep in dma_list] if dma_list else []
            ntb_list = BASE.execute_run(f'lspci -vvv | grep -B 10 -E "{ntb_vd}|SDTECH Device 2004" | grep "^[0-9a-f]"',
                             i_exit_code=True, i_record_cmd=True).get_origin_data().split("\n")
            ntb_ep_list = [key + ":"  + ntb_ep[0:7] for ntb_ep in ntb_list] if ntb_list else []
            for partition in sw:
                mep_dict = {}  # 构建mep字典
                dma_arr = []  # 构建dma字典
                ntb_dict = {}  # 构建ntb字典
                ep_list = []  # 构建ep列表
                for bdf in partition[1:]:
                    ep_bdf = []
                    bus_text = BASE.execute_run(f"lspci -vs {bdf} |grep Bus", i_exit_code=True, i_record_cmd=True).get_origin_data()
                    pattern = r'.*secondary=(.*),.*subordinate=(.*),.*'
                    res = re.findall(pattern, bus_text)
                    if not res:
                        continue  # iep的情况
                    secondary_bus, subordinate_bus = res[0]
                    if secondary_bus == subordinate_bus: #单bus号的ep
                        if BASE.execute_run(f"lspci -s {secondary_bus}:00.0", i_record_cmd=True).get_origin_data() != "":
                            ep_bdf.append(key + ":"  + secondary_bus + ":00.0")
                        else:
                            continue  # dsp下无ep的情况
                    else: #多bus号的ep，只取第一个bus号下的ep
                        ep_bdf.append(key + ":"  + f"{secondary_bus}:00.0")
                    driver_res = BASE.execute_run(
                        f"lspci -vvs {ep_bdf[0]} |grep 'driver in use' |awk -F ' ' '{{print $NF}}'", i_record_cmd=True).get_origin_data()
                    ep_vd = BASE.execute_run(f"lspci -ns {ep_bdf[0]} |awk -F ' ' '{{print $3}}'", i_record_cmd=True).get_origin_data()
                    for key_, value_ in eps.items():
                        if ep_vd == value_:
                            name = key_
                            break
                        else:
                            name = "NA"
                    if ep_bdf[0] in mep_ep_list:
                        mep_dict["dsp"] = bdf
                        mep_dict["ep"] = ep_bdf[0]
                        mep_dict["driver"] = driver_res
                        mep_dict["name"] = name
                    elif ep_bdf[0] in dma_ep_list:
                        dma_dict = {}
                        dma_dict["dsp"] = bdf
                        dma_dict["ep"] = ep_bdf[0]
                        dma_dict["driver"] = driver_res
                        dma_dict["name"] = name
                        dma_arr.append(dma_dict)
                    elif ep_bdf[0] in ntb_ep_list:
                        ntb_dict["dsp"] = bdf
                        ntb_dict["ep"] = ep_bdf[0]
                        ntb_dict["driver"] = driver_res
                        ntb_dict["name"] = name
                    else:
                        ep_list.append({'dsp': bdf, 'ep': ep_bdf[0], 'driver': driver_res, 'name': name})

                all_sudu_sw[key].append(
                    {'usp': partition[0], 'eps': ep_list, 'mep': mep_dict, 'dma': dma_arr, 'ntb': ntb_dict})
                # assert len(ep_list) != 0, "Env check fail, Not Find EP!"
                if len(ep_list) == 0:
                    print("Warning: Have a SW part not Find EP!")

        return all_sudu_sw

    def get_switch_info(self):
        if BASE.ssh is None:
            raise SSHSessionError("init BASE.ssh")


        devices = []
        parser = BASE.execute_run(f"lspci -Dvvvnnd 205e:5104| grep 'Upstream Port' -B 30 | egrep '..:..\.0' | cut -d ' ' -f 1", i_record_cmd=True)
        msg = parser.get_origin_data()
        usplist = msg.strip().split('\n')

        dma_p = []
        mep_p = []
        ntb_p = []
        for usp in usplist:
            sw_id = usplist.index(usp)
            uspbdf, dspbdf_list, epbdf_list = self.get_all_device(usp)
            rpbdf = self.get_parent_device(uspbdf)
            devices.append(self.get_device(rpbdf, 'RP', sw_id))
            devices.append(self.get_device(usp, 'USP', sw_id))
            for ep in epbdf_list:
                device = self.get_device(ep, 'EP', sw_id)
                if device.type == 'DMA':
                    dma_p.append(device.parent)
                elif device.type == 'MEP':
                    mep_p.append(device.parent)
                elif device.type == 'NTB':
                    ntb_p.append(device.parent)
                devices.append(device)
            for dsp in dspbdf_list:
                if dsp in dma_p:
                    device = self.get_device(dsp, 'DMA_IDSP', sw_id)
                elif dsp in mep_p:
                    device = self.get_device(dsp, 'MEP_IDSP', sw_id)
                elif dsp in ntb_p:
                    device = self.get_device(dsp, 'NTB_IDSP', sw_id)
                else:
                    device = self.get_device(dsp, 'DSP', sw_id)
                devices.append(device)

        return devices

    def get_all_device(self, bdf):
        """
        :param bdf: usp bdf
        :return:
        """
        parser = BASE.execute_run(
            f"ls -d /sys/bus/pci/devices/{bdf}/*/ | egrep '(([0-9a-f]+:)+[0-9a-f]{{2}}.[0-7]/){{2}}' | awk -F/ '{{print $(("
            f"NF-1))}}'", i_record_cmd=True)
        dsp = parser.get_origin_data()
        if 'No such file or directory' in dsp:
            dsp = []
        else:
            dsp = dsp.strip().split()

        parser = BASE.execute_run(
            f"ls -d /sys/bus/pci/devices/{bdf}/*/*/ | egrep '(([0-9a-f]+:)+[0-9a-f]{{2}}.[0-7]/){{3}}' | awk -F/ '{{print "
            f"$((NF-1))}}'", i_record_cmd=True)
        ep = parser.get_origin_data()
        if 'No such file or directory' in ep:
            ep = []
        else:
            ep = ep.strip().split()

        return [bdf, dsp, ep]

    def get_device(self, bdf, Type, switch_id):
        device = namedtuple('device', ['device_bdf', 'device_id', 'vendor_id', 'type', 'class_code',
                                       'cap_speed', 'cap_width', 'current_speed', 'current_width', 'driver', 'slot',
                                       'parent', 'children', "aer_status", "switch_id"])
        bdf_mod = bdf[5:12] if bdf[0:3] == '000' else bdf
        all_info = BASE.execute_run(f'lspci -vvvns {bdf_mod} | grep -E "({bdf_mod}|LnkCap:|LnkSta:|Kernel driver|Physical Slot|Subsystem)"', i_record_cmd=True).get_origin_data()
        class_code, vendor_id, device_id = re.search(f"{bdf_mod}\s+(.+?):\s+(.+?):(\\w+)", all_info).groups()
        if re.search(r"LnkCap:.*?Speed\s+(.+?),\s+Width\s+x(.+?),.*?LnkSta:\s+Speed\s+(.+?)\s+.*?Width\s+x(.+?)\s+", all_info, flags=re.S):
            cap_speed, cap_width, current_speed, current_width = re.search(r"LnkCap:.*?Speed\s+(.+?),\s+Width\s+x(.+?),.*?LnkSta:\s+Speed\s+(.+?)\s+.*?Width\s+x(.+?)\s+", all_info, flags=re.S).groups()
        else:
            cap_speed, cap_width, current_speed, current_width = "Null", "Null", "Null", "Null"
        if re.search(r"Subsystem:\s+(.+)", all_info):
            sub_id = re.search(r"Subsystem:\s+(.+)", all_info).group(1)
        else:
            sub_id = "Null"
        if re.search(r"Kernel\s+driver\s+in\s+use:\s+(.+)", all_info):
            driver = re.search(f"Kernel\s+driver\s+in\s+use:\s+(.+)", all_info).group(1)
        else:
            driver = "Null"
        if re.search(r"Physical\s+Slot:\s+(.+)", all_info):
            slot = re.search(f"Physical\s+Slot:\s+(.+)", all_info).group(1)
        else:
            slot = "Null"
        parent = self.get_parent_device(bdf)
        children = self.get_children_device(bdf)
        aer_status = self.get_aer_status_info(bdf)
        if Type == 'EP':
            if f'{sub_id}' == '205e:2005':
                Type = 'DMA'
            if f'{sub_id}' == '205e:2006':
                Type = 'MEP'
            if f'{sub_id}' == '205e:2004':
                Type = 'NTB'
        return device(bdf, device_id, vendor_id, Type, class_code, cap_speed,
                      cap_width, current_speed, current_width, driver, slot, parent, children, aer_status, switch_id)

    def parse_cesta(self, cesta_hex):
        if not cesta_hex or not re.match(r'^[0-9A-Fa-f]+$', cesta_hex):
            return ''

        v = int(cesta_hex, 16)
        flags = [
            ("RxErr", 0),
            ("BadTLP", 6),
            ("BadDLLP", 7),
            ("Rollover", 8),
            ("Timeout", 12),
            ("AdvNonFatalErr", 13),
        ]
        parts = []
        for name, bit in flags:
            parts.append(f"{name}{['-', '+'][(v >> bit) & 1]}")
        return " ".join(parts)

    def parse_devsta(self, devsta_hex):
        if not devsta_hex or not re.match(r'^[0-9A-Fa-f]+$', devsta_hex):
            return ''
        v = int(devsta_hex, 16)
        flags = [
            ("CorrErr", 0),
            ("NonFatalErr", 1),
            ("FatalErr", 2),
            ("UnsupReq", 3),
            ("AuxPwr", 4),
            ("TransPend", 5),
        ]
        parts = []
        for name, bit in flags:
            parts.append(f"{name}{['-', '+'][(v >> bit) & 1]}")
        return " ".join(parts)

    def parse_uesta(self, uesta_hex):
        if not uesta_hex or not re.match(r'^[0-9A-Fa-f]+$', uesta_hex):
            return ''
        v = int(uesta_hex, 16)
        flags = [
            ("DLP", 0),
            ("SDES", 1),
            ("TLP", 2),
            ("FCP", 3),
            ("CmpltTO", 4),
            ("CmpltAbrt", 5),
            ("UnxCmplt", 6),
            ("RxOF", 7),
            ("MalfTLP", 8),
            ("ECRC", 9),
            ("UnsupReq", 10),
            ("ACSViol", 13),
        ]
        parts = []
        for name, bit in flags:
            parts.append(f"{name}{['-', '+'][(v >> bit) & 1]}")
        return " ".join(parts)

    def get_aer_status_info(self, bdf):
        devsta = BASE.execute_run(f"setpci -s {bdf} CAP_EXP+0x0a.w", i_record_cmd=True).get_origin_data()
        uesta = BASE.execute_run(f"setpci -s {bdf} ECAP_AER+0x04.l", i_exit_code=True, i_record_cmd=True).get_origin_data()
        ret_ue = BASE.ssh.get_exit_code()
        cesta = BASE.execute_run(f"setpci -s {bdf} ECAP_AER+0x10.l", i_exit_code=True, i_record_cmd=True).get_origin_data()
        ret_ce = BASE.ssh.get_exit_code()
        if ret_ue != 0:
            uesta = 'aer cap not found'
        if ret_ce != 0:
            cesta = 'aer cap not found'
        return {
            'DevSta': self.parse_devsta(devsta.strip()),
            'UESta': self.parse_uesta(uesta.strip()),
            'CESta': self.parse_cesta(cesta.strip()),
        }

    def get_vendor_deviceid(self, bdf):
        parser = BASE.execute_run(f"lspci -ns {bdf} | awk '{{print $3}}'")
        msg = parser.get_origin_data()
        vendor_id, device_id = msg.strip().split(':')
        return f"{vendor_id}", f"{device_id}"

    def get_parent_device(self, bdf):
        msg = BASE.execute_run(
            f"ls -d /sys/bus/pci/devices/*/{bdf}/ | egrep '(([0-9a-f]+:)+[0-9a-f]{{2}}.[0-7]/){{2}}' | awk "
            f"-F/ '{{print $((NF-2))}}'", i_record_cmd=True).get_origin_data()
        if 'No such file or directory' in msg:
            msg = ''
        else:
            msg = msg.strip()
        return msg

    def get_children_device(self, bdf):
        msg = BASE.execute_run(
            f"ls -d /sys/bus/pci/devices/{bdf}/*/ | egrep '(([0-9a-f]+:)+[0-9a-f]{{2}}.[0-7]/){{2}}' | awk "
            f"-F/ '{{print $((NF-1))}}'", i_record_cmd=True).get_origin_data()
        if 'No such file or directory' in msg:
            msg = []
        else:
            msg = msg.strip().split()
        return msg

    def get_classcode(self, bdf):
        class_code = BASE.execute_run(f"cat /sys/bus/pci/devices/{bdf}/class").get_origin_data()
        return class_code

    def get_speed_width(self, bdf):
        current = BASE.execute_run(f"lspci -vvvs {bdf} | grep LnkSta: | awk '{{print $3\" \"$6}}'").get_origin_data()
        current = current.strip().split()
        cap = BASE.execute_run(f"lspci -vvvs {bdf} | grep LnkCap: | awk '{{print $5\" \"$7}}'").get_origin_data()
        cap = cap.strip().replace(',', ' ').split()
        return cap + current

    def get_driver(self, bdf):
        msg = BASE.execute_run(
            f"lspci -ks {bdf} | grep -i 'Kernel driver in use:' | awk '{{print $5}}'").get_origin_data()

        return msg.strip()

    def get_slot(self, bdf):
        msg = BASE.execute_run(f"lspci -vvvs {bdf} | grep -i 'Physical Slot:' | awk '{{print $3}}'").get_origin_data()

        return msg.strip()

    def sbr_set(self, bdf):
        if BASE.ssh is None:
            raise SSHSessionError("init BASE.ssh")
        _ret = 0
        LOGGER.info(f"read data from BDF:{bdf}")
        orgdata = BASE.execute_run(f"setpci -s {bdf} BRIDGE_CONTROL.w").get_origin_data()
        BASE.execute_run(f"setpci -s {bdf} BRIDGE_CONTROL.w={hex(int(orgdata, 16) | (1 << 6))}")
        time.sleep(1)
        BASE.execute_run(f"setpci -s {bdf} BRIDGE_CONTROL.w={hex(int(orgdata, 16) & ~(1 << 6))}")
        time.sleep(5)
        LOGGER.info(f"reset {bdf} success")

    def read_config_lspci(self, bdf):
        res = BASE.execute_run(f"hexdump /sys/bus/pci/devices/{bdf}/config").get_origin_data()
        if res.split('\n')[0].split()[1] == "ffff":
            return False
        else:
            return True

    def save_data_file(self, data, filename):
        data = [d._asdict() for d in data]
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, sort_keys=True)

    def setpci_bits(self, bdf, offset, bit_start, bit_end, value, width="B"):
        assert width in ("B", "W", "L"), "width must be one of B, W, L"
        bytes_map = {"B": 1, "W": 2, "L": 4}

        read_cmd = f"setpci -s {bdf} {offset}.{width}"
        orig_val = int(BASE.execute_run(read_cmd).get_origin_data(), 16)
        total_bits = bytes_map[width] * 8

        # 校验位范围
        if not (0 <= bit_end <= bit_start < total_bits):
            raise ValueError(f"位范围 {bit_start}:{bit_end} 对于宽度 '{width}' 无效")
        # 创建一个在 bit_start 和 bit_end 之间全为 1 的掩码
        mask = ((1 << (bit_start - bit_end + 1)) - 1) << bit_end
        # 清除原始值中的目标位，然后或上移位后的新值
        new_val = (orig_val & ~mask) | ((value << bit_end) & mask)

        hex_val = f"{new_val:0{bytes_map[width] * 2}x}"
        write_cmd = f"setpci -s {bdf} {offset}.{width}={hex_val}"
        BASE.execute_run(write_cmd)
        print(f"[OK] {bdf} {offset}.{width}: {orig_val:#x} -> {new_val:#x}")

    def speed_change(self, dsp, gen):
        """
            修改 PCIe 链路速率 (Target Link Speed)
            :param bdf: PCI 设备地址，如 "0000:17:00.0"
            :param gen: 目标代际 (1=Gen1, 2=Gen2, 3=Gen3, 4=Gen4, 5=Gen5)
        """
        assert gen in (1, 2, 3, 4, 5), "gen must be 1~5"
        LOGGER.info(f"修改{dsp}对应链路速率为gen{gen}")
        self.setpci_bits(dsp, "CAP_EXP+30", 3, 0, gen)
        self.link_retrain(dsp)

    def link_retrain(self, dsp):
        """
            触发 PCIe 链路重新训练 (Link Retrain)
            :param bdf: PCI 设备地址，如 "0000:17:00.0"
        """
        LOGGER.info(f"重训练{dsp}对应链路")
        self.setpci_bits(dsp, "CAP_EXP+10", 5, 5, 1)
    def flr(self, bdf):
        """
            执行 PCIe 功能级复位 (Function Level Reset, FLR)
            :param bdf: PCI 设备地址，如 "0000:17:00.0"
        """
        LOGGER.info(f"对{bdf}执行功能级复位")
        self.setpci_bits(bdf, "CAP_EXP+8", 15, 15, 1, width="W")
    def set_bme(self, bdf, enable=True):
        """
            启用或禁用 PCIe 总线主控 (Bus Master Enable, BME)
            :param bdf: PCI 设备地址，如 "0000:17:00.0"
            :param enable: True 启用，False 禁用
        """
        action = "启用" if enable else "禁用"
        LOGGER.info(f"{action}{bdf}对应总线主控")
        self.setpci_bits(bdf, "COMMAND", 2, 2, int(enable))

    def devmem2_read(self, address, width="b"):
        """
            使用 devmem2 工具读取物理内存地址
            :param address: 物理内存地址，如 0xFEDC0000
            :param width: 读取宽度，b, h, w
            :return: 读取的值
        """
        cmd = f"devmem2 0x{address} {width}"
        output = BASE.execute_run(cmd).get_origin_data()
        match = re.search(r"\): (0x[0-9a-fA-F]+)", output)
        if match:
            return match.group(1)
        else:
            raise ValueError("Failed to read memory address")
    def get_bar_address(self, bdf, bar_num=0):
        """
            获取 PCIe 设备的 BAR 地址
            :param bdf: PCI 设备地址，如 "0000:17:00.0"
            :param bar_num: BAR编号，0-5
            :return: BAR地址
        """
        if not (0 <= bar_num <= 5):
            raise ValueError("bar_num must be between 0 and 5")
        cmd = f"lspci -s {bdf} -vvv | grep 'Region {bar_num}:'"
        output = BASE.execute_run(cmd).get_origin_data()
        match = re.search(r"Region {}: Memory at ([0-9a-fA-F]+)".format(bar_num), output)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"Failed to get BAR{bar_num} address for {bdf}")

    def set_power_state(self, bdf, state):
        """
            设置 PCIe 设备的电源状态
            :param bdf: PCI 设备地址，如 "0000:17:00.0"
            :param state: 目标电源状态，如 "D0", "D1", "D2", "D3hot", "D3cold"
        """
        valid_states = {"D0": 0, "D1": 1, "D2": 2, "D3hot": 3, "D3cold": 4}
        if state not in valid_states:
            raise ValueError(f"Invalid power state: {state}")
        LOGGER.info(f"设置{bdf}对应电源状态为{state}")
        self.setpci_bits(bdf, "CAP_PM+4", 1, 0, valid_states[state])

    def get_cx7_devices(self):
        """
            获取系统中所有CX7设备的信息
            :return: 包含CX7设备信息的列表
        """
        devices = BASE.execute_run("ibdev2netdev").get_origin_data().strip().split("\n")
        rdmalink_devices = [line.split()[0] for line in devices]
        ip_devices = [line.split()[4] for line in devices]
        return {"rdmalink": rdmalink_devices, "ip": ip_devices}

    def net_test_set_up(self, ip_devices):
        """
            网络测试环境准备
            :param ip_devices: IP设备列表
        """
        for i in range(len(ip_devices)):
            BASE.execute_run(f"ip netns add ns{i}")
            BASE.execute_run(f"ip link set {ip_devices[i]} netns ns{i}")
            BASE.execute_run(f"ip netns exec ns{i} ip addr add 100.1.1.{i}/24 dev {ip_devices[i]}")
            BASE.execute_run(f"ip netns exec ns{i} ip link set {ip_devices[i]} up")

    def start_opensm(self):
        """
            启动OpenSM子网管理器
        """
        list1 = BASE.execute_run("ibstat |grep 'Port GUID'|awk '{print $NF}'").get_origin_data().strip().split("\n")
        for i in list1:
            BASE.execute_run(f"opensm -g {i} -B -p 14")

    def cx7_start_server(self, rdmalink_devices):
        """
            启动CX7服务端
            :param rdmalink_device: RDMA名称
        """
        for i in range(len(rdmalink_devices)):
            BASE.execute_run(f"ip netns exec ns{i} ib_send_bw --report_gbits --run_infinitely --cpu_util -d mlx5_{i} -FD2 -q 4 -m 4096 -s 512K &>/dev/null &")

    def cx7_start_client(self, rdmalink_devices):
        """
            启动CX7客户端
            :param rdmalink_device: RDMA名称
        """
        for i in range(len(rdmalink_devices)):
            for j in range(len(rdmalink_devices)):
                if j != i:
                    remote_ip = f"100.1.1.{j}"
                    BASE.execute_run(f"ip netns exec ns{i} ping -c 2 -W 1 {remote_ip}", i_exit_code=True)
                    if BASE.ssh.get_exit_code() == 0:
                        LOGGER.info(f"发现可达IP{remote_ip}")
                        BASE.execute_run(f"ip netns exec ns{i} ib_send_bw --report_gbits --run_infinitely --cpu_util -d mlx5_{i} -FD2 -q 4 -m 4096 -s 512K {remote_ip} &>/dev/null &")
                        break
            else:
                LOGGER.info(f"未发现可达IP，无法启动客户端{rdmalink_devices[i]}")

    def clear_netns(self):
        """
            清理网络命名空间
        """
        namespaces = BASE.execute_run("ip netns list").get_origin_data().strip().split("\n")
        for ns in namespaces:
            ns_name = ns.split()[0]
            if ns_name != "Null":
                BASE.execute_run(f"ip netns delete {ns_name}")
            else:
                LOGGER.info("未发现网络命名空间，无需清理")

    def kill_ib_process(self):
        """
            杀死所有ib进程
        """
        LOGGER.info("杀死所有ib进程")
        BASE.execute_run("killall ib_send_bw ib_send_lat ib_write_bw ib_write_lat ib_read_bw ib_read_lat ib_atomic_bw ib_atomic_lat", i_exit_code=True)

    def upload_file_to_server(self, src_file, des_file, host, username,
                              password, port="22"):
        """
        向远程服务器传送文件
        :param src_file: 本地文件路径
        :param des_file: 远程主机的文件路径
        :param host: 主机名
        :param username: 用户名
        :param password: 密码
        :param port: 端口
        :return flag: True|False
        @Author: wuhao
        """
        try:
            LOGGER.info("【向远程主机{}上位置{}, 传送文件{}】".format(host, des_file, src_file))
            self.trans_client = paramiko.Transport((host, int(port)))
            self.trans_client.connect(username=username, password=password)
            self.sftp = paramiko.SFTPClient.from_transport(self.trans_client)
            self.sftp.put(src_file, des_file)
            self.trans_client.close()
            LOGGER.info("【向远程主机传送文件{}成功】".format(src_file))
            return True
        except Exception as e:
            LOGGER.error("【向远程主机传送文件{}异常】".format(src_file))
            LOGGER.error(traceback.format_exc())
            return False
    def link_enable(self, dsp, enable=True):
        """
            启用PCIe设备的链路
            :param dsp: PCI设备地址，如 "0000:17:00.0"
        """
        if enable == True:
            LOGGER.info(f"启用{dsp}对应链路")
            self.setpci_bits(dsp, "CAP_EXP+10", 4, 4, 0)
        else:
            LOGGER.info(f"关闭{dsp}对应链路")
            self.setpci_bits(dsp, "CAP_EXP+10", 4, 4, 1)
    def get_pm_state(self, bdf):
        """
            获取PCIe设备的电源状态
            :param bdf: PCI设备地址，如 "0000:17:00.0"
            :return: 电源状态字符串，如 "D0", "D1", "D2", "D3hot", "D3cold"
        """
        res = BASE.execute_run(f"lspci -vvvs {bdf}|grep -A 2 'Power Management'|grep Status|awk '{{print$2}}'").get_origin_data()
        return res
    def get_pm_suport_pme_states(self, bdf):
        """
            获取PCIe设备能生成PME的电源状态列表
            :param bdf: PCI设备地址，如 "0000:17:00.0"
            :return: 能生成PME的电源状态列表，如 ["D0", "D1", "D2", "D3hot", "D3cold"]
        """
        res = BASE.execute_run(f"lspci -vvvs {bdf}|grep -A 2 'Power Management'|grep Flags|awk '{{print$7}}'").get_origin_data()
        cap = re.findall(r"([\d|a-zA-z]+)\+", res)
        LOGGER.info("能生成PME的电源状态列表有: {}".format(cap))
        return cap

    def ASPM_enable(self, bdf, L0s=True, L1=True):
        """
            启用或禁用PCIe设备的ASPM
            :param bdf: PCI设备地址，如 "0000:17:00.0"
            :param True启用，False禁用
        """
        LOGGER.info(f"启用或禁用{bdf}对应ASPM")
        if L0s:
            self.setpci_bits(bdf, "CAP_EXP+10", 0, 0, 1)
        else:
            self.setpci_bits(bdf, "CAP_EXP+10", 0, 0, 0)
        if L1:
            self.setpci_bits(bdf, "CAP_EXP+10", 1, 1, 1)
        else:
            self.setpci_bits(bdf, "CAP_EXP+10", 1, 1, 0)

    def PME_enable(self, bdf, PME=True):
        """
            启用或禁用PCIe设备的PME
            :param bdf: PCI设备地址，如 "0000:17:00.0"
            :param True启用，False禁用
        """
        LOGGER.info(f"启用或禁用{bdf}对应PME")
        if PME:
            self.setpci_bits(bdf, "CAP_PM+4", 8, 8, 1, width="W")
        else:
            self.setpci_bits(bdf, "CAP_PM+4", 8, 8, 0, width="W")

    def perform_equalization_enable(self, dsp, perform_eq=True):
        """
            PCIe链路均衡使能或禁止
        """
        LOGGER.info(f"执行{dsp}对应链路均衡使能或禁止")
        if perform_eq:
            self.setpci_bits(dsp, "ECAP_SECPCI+4", 0, 0, 1)
        else:
            self.setpci_bits(dsp, "ECAP_SECPCI+4", 0, 0, 0)

    def clear_aer_status(self, bdf):
        """
            清除PCIe设备的AER状态
            :param bdf: PCI设备地址，如 "0000:17:00.0"
        """
        LOGGER.info(f"清除{bdf}对应AER状态")
        self.setpci_bits(bdf, "CAP_EXP+0A", 7, 0, 2**8 - 1, width="B")
        self.setpci_bits(bdf, "ECAP_AER+04", 31, 0, 2**32 - 1, width="L")
        self.setpci_bits(bdf, "ECAP_AER+10", 15, 0, 2**16 - 1, width="W")

    def pci_rescan(self):
        """
            触发PCI总线重新扫描
        """
        LOGGER.info("触发PCI总线重新扫描")
        BASE.execute_run("echo 1 > /sys/bus/pci/rescan")

    def npem_enable(self, bdf, enable=True):
        """
            启用或禁用PCIe设备的NPEM
            :param bdf: PCI设备地址，如 "0000:17:00.0"
            :param enable: True启用，False禁用
        """
        action = "启用" if enable else "禁用"
        LOGGER.info(f"{action}{bdf}对应NPEM")
        if enable:
            self.setpci_bits(bdf, "ECAP_NPEM+8", 0, 0, 1)
        else:
            self.setpci_bits(bdf, "ECAP_NPEM+8", 0, 0, 0)

    def ini_npem_reset(self, bdf):
        """
            触发PCIe设备的NPEM复位
            :param bdf: PCI设备地址，如 "0000:17:00.0"
        """
        LOGGER.info(f"触发{bdf}对应NPEM复位")
        self.setpci_bits(bdf, "ECAP_NPEM+8", 1, 1, 1)

    def npem_control(self, bdf, type):
        """
            控制PCIe设备的NPEM功能
            :param bdf: PCI设备地址，如 "0000:17:00.0"
            :param type: 操作类型，如下
        """
        if type == "OK":
            BASE.execute_run(f"setpci -s {bdf} ECAP_NPEM+8.W=0005")
        elif type == "Locate":
            BASE.execute_run(f"setpci -s {bdf} ECAP_NPEM+8.W=0009")
        elif type == "Fail":
            BASE.execute_run(f"setpci -s {bdf} ECAP_NPEM+8.W=0011")
        elif type == "Rebuild":
            BASE.execute_run(f"setpci -s {bdf} ECAP_NPEM+8.W=0021")
        elif type == "PFA":
            BASE.execute_run(f"setpci -s {bdf} ECAP_NPEM+8.W=0041")
        elif type == "Hot Spare":
            BASE.execute_run(f"setpci -s {bdf} ECAP_NPEM+8.W=0081")
        elif type == "A Critical Array":
            BASE.execute_run(f"setpci -s {bdf} ECAP_NPEM+8.W=0101")
        elif type == "A Failed Array":
            BASE.execute_run(f"setpci -s {bdf} ECAP_NPEM+8.W=0201")
        else:
            raise ValueError("Invalid NPEM control type")

    def get_nvme_symbolic_name(self, bdf):
        """
            获取nvme设备对应的磁盘符号链接名称
            :param bdf: PCI设备地址，如 "0000:17:00.0"
            :return: 磁盘符号链接名称，如 "/dev/nvme0n1"
        """
        ret = BASE.execute_run(f"ls /sys/bus/pci/devices/{bdf}/nvme").get_origin_data().strip()
        nvme_name = f"/dev/{ret}n1"
        LOGGER.info(f"获取到的盘符为：{nvme_name}")
        return nvme_name