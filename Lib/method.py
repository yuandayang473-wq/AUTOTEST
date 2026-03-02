import json
import os
import re
import time
from collections import defaultdict, namedtuple

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
        :return {'0000': [{'usp': '71:00.0', 'eps': [{'dsp': '72:04.0', 'ep': '77:00.0', 'driver': 'nvme', 'name': 'NA'}, {'dsp': '72:05.0', 'ep': '78:00.0', 'driver': 'nvme', 'name': 'EP_SSD_WDAN1500'}], 'mep': {'dsp': '72:1c.0', 'ep': '79:00.0', 'driver': 'nvme', 'name': 'NA'}, 'dma': [{'dsp': '72:1d.0', 'ep': '7a:00.0', 'driver': 'Null', 'name': 'NA'}, {'dsp': '72:1e.0', 'ep': '7b:00.0', 'driver': 'Null', 'name': 'NA'}], 'ntb': {}}]}
        """
        # 读取vendor.yml
        vendor_file = os.path.abspath(os.path.join(os.path.abspath(__file__), "../")) + "/vendor.yml"
        with open(vendor_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            sw_vd = data["SW_VD"]
            mep_vd = data["EP_SWITCH_SUDU_MEP"]
            mep_dsp_vd = data["DSP_MEP_VD"]
            dma_vd = data["EP_SWITCH_SUDU_DMA"]
            dma_dsp_vd = data["DSP_DMA_VD"]  # 列表
            ntb_vd = data["EP_SWITCH_SUDU_NTB"]
            ntb_dsp_vd = data["DSP_NTB_VD"]
            eps = data["EPS"]

        # 根据vendor id找到所有属于数渡sw的设备以及bridge
        sudu_sw = BASE.execute_run("lspci -Dd 205e:").get_origin_data()
        assert sudu_sw, "Not find any switch in system!"
        # 按照domain进行分类
        dict_all = defaultdict(list)
        for line in sudu_sw.splitlines():
            domain = line[:4]
            dict_all[domain].append(line)
        for key, value in dict_all.items():
            sudu_sw = value
            # 判断是否为合成模式
            sw_bdf = [i[5:12] for i in sudu_sw]
            usp = []
            sw = []
            for index, bdf in enumerate(sw_bdf):
                BASE.execute_run(f"lspci -vs {bdf} |grep -w Upstream", save_exit_code=True)
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
            mep_res = BASE.execute_run(f"lspci -Dd {mep_vd}").get_origin_data()
            if mep_res[5:12] in sw[0]:
                pass  # 第一个switch有mep,无需操作
            else:
                sw[0], sw[1] = sw[1], sw[0]  # 带mep的switch放到首位置
            # sw_bdf = [{'usp': xxx,
            # 'eps': [{'dsp': xxx,'ep': xxx,'driver': xxx,'name': xxx},{}...],
            # 'mep': {'dsp': xxx, 'ep': xxx, 'driver': xxx},
            # 'dma': [{'dsp': xxx, 'ep': xxx, 'driver': xxx},{}...],
            # 'ntb': {'dsp': xxx, 'ep': xxx, 'driver': xxx}, {}]
            all_sudu_sw = defaultdict(list)
            mep_ep = mep_res[5:12]
            dma_ep_list = [dma_ep[5:12] for dma_ep in
                           BASE.execute_run(f"lspci -Dd {dma_vd} |awk -F ' ' '{{print $1}}'").get_origin_data().split()]
            ntb_ep_list = [ntb_ep[5:12] for ntb_ep in
                           BASE.execute_run(f"lspci -Dd {ntb_vd} |awk -F ' ' '{{print $1}}'").get_origin_data().split()]

            for partition in sw:
                mep_dict = {}  # 构建mep字典
                dma_arr = []  # 构建dma字典
                ntb_dict = {}  # 构建ntb字典
                ep_list = []  # 构建ep列表
                for bdf in partition[1:]:
                    ep_bdf = []
                    bus_text = BASE.execute_run(f"lspci -vs {bdf} |grep Bus", i_exit_code=True).get_origin_data()
                    pattern = r'.*secondary=(.*),.*subordinate=(.*),.*'
                    res = re.findall(pattern, bus_text)
                    if not res:
                        continue  # iep的情况
                    secondary_bus, subordinate_bus = res[0]
                    if secondary_bus == "00":
                        continue
                    elif secondary_bus == subordinate_bus:
                        if BASE.execute_run(f"lspci -s {secondary_bus}:00.0").get_origin_data() != "Null":
                            ep_bdf.append(secondary_bus + ":00.0")
                        else:
                            continue  # dsp下无ep的情况
                    else:
                        ep_bdf.append(f"{secondary_bus}:00.0")
                    driver_res = BASE.execute_run(
                        f"lspci -vvs {ep_bdf[0]} |grep 'driver in use' |awk -F ' ' '{{print $NF}}'").get_origin_data()
                    ep_vd = BASE.execute_run(f"lspci -ns {ep_bdf[0]} |awk -F ' ' '{{print $3}}'").get_origin_data()
                    for key_, value_ in eps.items():
                        if ep_vd == value_:
                            name = key_
                            break
                        else:
                            name = "NA"
                    if ep_bdf[0] == mep_ep:
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
        parser = BASE.execute_run(f"lspci -Dnd '205e': | awk '{{if($2==\"0604:\")print $1}}'")
        msg = parser.get_origin_data()
        switchinfo = msg.strip().split('\n')

        usplist = []

        for dev in switchinfo:
            BASE.execute_run(f"lspci -vvvs {dev} | grep -i 'Upstream Port'", save_exit_code=True)
            if BASE.ssh.get_exit_code() == 0:
                usplist.append(dev)

        dma_p = []
        mep_p = ''
        for usp in usplist:
            uspbdf, dspbdf_list, epbdf_list = self.get_all_device(usp)
            devices.append(self.get_device(usp, 'USP'))
            for ep in epbdf_list:
                device = self.get_device(ep, 'EP')
                if device.type == 'DMA':
                    dma_p.append(device.parent)
                elif device.type == 'MEP':
                    mep_p = device.parent
                devices.append(device)
            for dsp in dspbdf_list:
                if dsp in dma_p:
                    device = self.get_device(dsp, 'DMA_IDSP')
                elif dsp == mep_p:
                    device = self.get_device(dsp, 'MEP_IDSP')
                else:
                    device = self.get_device(dsp, 'DSP')
                devices.append(device)

        return devices

    def get_all_device(self, bdf):
        """
        :param bdf: usp bdf
        :return:
        """
        parser = BASE.execute_run(
            f"ls -d /sys/bus/pci/devices/{bdf}/*/ | egrep '(([0-9a-f]+:)+[0-9a-f]{{2}}.[0-7]/){{2}}' | awk -F/ '{{print $(("
            f"NF-1))}}'")
        dsp = parser.get_origin_data()
        if 'No such file or directory' in dsp:
            dsp = []
        else:
            dsp = dsp.strip().split()

        parser = BASE.execute_run(
            f"ls -d /sys/bus/pci/devices/{bdf}/*/*/ | egrep '(([0-9a-f]+:)+[0-9a-f]{{2}}.[0-7]/){{3}}' | awk -F/ '{{print "
            f"$((NF-1))}}'")
        ep = parser.get_origin_data()
        if 'No such file or directory' in ep:
            ep = []
        else:
            ep = ep.strip().split()

        return [bdf, dsp, ep]

    def get_device(self, bdf, Type):
        device = namedtuple('device', ['device_bdf', 'device_id', 'vendor_id', 'type', 'class_code',
                                       'cap_speed', 'cap_width', 'current_speed', 'current_width', 'driver', 'slot',
                                       'parent', 'children', "aer_status"])
        bdf_mod = bdf[5:12] if bdf[0:3] == '000' else bdf
        all_info = BASE.execute_run(f'lspci -vvvns {bdf_mod} | grep -E "({bdf_mod}|LnkCap:|LnkSta:|Kernel driver|Physical Slot)"').get_origin_data()
        class_code, vendor_id, device_id = re.search(f"{bdf_mod}\s+(.+?):\s+(.+?):(\\w+)", all_info).groups()
        cap_speed, cap_width, current_speed, current_width = re.search(r"LnkCap:.*?Speed\s+(.+?),\s+Width\s+x(.+?),.*?LnkSta:\s+Speed\s+(.+?)\s+.*?Width\s+x(.+?)\s+", all_info, flags=re.S).groups()
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
            if f'{vendor_id}:{device_id}' == '205e:0020':
                Type = 'DMA'
            if f'{vendor_id}:{device_id}' == '205e:0030':
                Type = 'MEP'
        return device(bdf, device_id, vendor_id, Type, class_code, cap_speed,
                      cap_width, current_speed, current_width, driver, slot, parent, children, aer_status)

    def expand_pci_addr(self, pci_addr):
        """
        Convert a possibly shortened PCI address to its expanded form, including
        normalizing the formatting of long addresses
        """

        m1 = LONG_PCI_ADDR_REGEX.match(pci_addr)
        m2 = SHORT_PCI_ADDR_REGEX.match(pci_addr)

        if m1:
            domain, bus, device, function = map(lambda n: int(n, 16), m1.groups())
            return "{:04x}:{:02x}:{:02x}.{:x}".format(domain, bus, device, function)
        if m2:
            bus, device, function = map(lambda n: int(n, 16), m2.groups())
            return "{:04x}:{:02x}:{:02x}.{:x}".format(0, bus, device, function)
        return None

    def get_aer_status_info(self, bdf):
        aer_info = {}
        device_name = self.expand_pci_addr(bdf)
        if not device_name:
            return None
        stat_names = ["aer_dev_correctable", "aer_dev_fatal", "aer_dev_nonfatal"]
        for stat_name in stat_names:
            filename = SYSFS_PCI_BUS_DEVICES + device_name + "/" + stat_name
            res = BASE.execute_run(f"if [ -f {filename} ]; then cat {filename}; fi").get_origin_data()
            if res == "Null":
                continue
            else:
                stats = {}
                for line in res.split("\n"):
                    key, value = line.strip().split()
                    stats[key] = int(value)
                aer_info[stat_name] = stats

        if len(aer_info) == 0:
            return None
        return aer_info

    def get_vendor_deviceid(self, bdf):
        parser = BASE.execute_run(f"lspci -ns {bdf} | awk '{{print $3}}'")
        msg = parser.get_origin_data()
        vendor_id, device_id = msg.strip().split(':')
        return f"{vendor_id}", f"{device_id}"

    def get_parent_device(self, bdf):
        msg = BASE.execute_run(
            f"ls -d /sys/bus/pci/devices/*/{bdf}/ | egrep '(([0-9a-f]+:)+[0-9a-f]{{2}}.[0-7]/){{2}}' | awk "
            f"-F/ '{{print $((NF-2))}}'").get_origin_data()
        if 'No such file or directory' in msg:
            msg = ''
        else:
            msg = msg.strip()
        return msg

    def get_children_device(self, bdf):
        msg = BASE.execute_run(
            f"ls -d /sys/bus/pci/devices/{bdf}/*/ | egrep '(([0-9a-f]+:)+[0-9a-f]{{2}}.[0-7]/){{2}}' | awk "
            f"-F/ '{{print $((NF-1))}}'").get_origin_data()
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
        BASE.execute_run(f"lspci -vvvs {bdf} | grep 'Unknown header type'", cmd_timeout=120, save_exit_code=True)

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
        cmd = f"devmem2 {hex(address)} {width}"
        output = BASE.execute_run(cmd).get_origin_data()
        match = re.search(r"Value at address .* \(0x[0-9a-fA-F]+\) is (0x[0-9a-fA-F]+)", output)
        if match:
            return match.group(1)
        else:
            raise ValueError("Failed to read memory address")
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
        devices = BASE.execute_run("ibdev2netdev").get_origin_data().split("\n")
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