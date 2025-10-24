# -*- coding: utf-8 -*-
import os
import re
import subprocess
import json
import time
# import pexpect
# import openpyxl
import logging
import configparser

import yaml


def execute_command(command):
    """
    执行终端命令,输出内容
    :param command:输入的命令
    :return:命令执行内容输出
    """
    # cmd="echo 1 |"+"sudo -S "+command
    # print(command)
    p = subprocess.Popen(command,
                         shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         text=True
                         # encoding='utf-8').stdout.read().split("\n"),
                         )
    out_msg = p.stdout.read().rstrip('\n')
    err_msg = p.stderr.read().rstrip('\n')
    # print(err_msg) debug
    # print(out_msg)

    if err_msg:
        if isinstance(err_msg, bytes):
            err_msg = err_msg.decode('utf-8')
        return err_msg
    else:
        if isinstance(out_msg, bytes):
            out_msg = out_msg.decode('utf-8')
        return out_msg


def get_bdf():
    """
    查找所有SW上usp,mep,dma,ntb,ep及dsp信息
    :return sw_bdf = [{'usp': xxx,
            'eps': [{'dsp': xxx,'ep': xxx,'driver': xxx,'name': xxx},{}...],
            'mep': {'dsp': xxx, 'ep': xxx, 'driver': xxx},
            'dma': [{'dsp': xxx, 'ep': xxx, 'driver': xxx},{}...],
            'ntb': {'dsp': xxx, 'ep': xxx, 'driver': xxx}, {},}
            {'usp': xxx, 'eps':[{},{}...],...}]
    """
    # 读取vendor.yml
    vendor_file = os.path.abspath(os.path.join(os.path.abspath(__file__), "../")) + "/vendor.yml"
    with open(vendor_file, "r") as f:
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
    sudu_sw = execute_command(r"lspci -Dd 205e:")
    assert sudu_sw, "Not find any switch in system!"
    # 判断是否在同domain下
    domain = [i[:4] for i in sudu_sw.splitlines()]
    sw = []
    if len(set(domain)) == 1:
        # 判断是否为合成模式
        sw_bdf = [i[5:12] for i in sudu_sw.splitlines()]
        usp = []
        for index, bdf in enumerate(sw_bdf):
            check_usp = execute_command(f"lspci -vs {bdf} |grep -w Upstream")
            if check_usp:
                usp.append({"bdf": bdf, "index": index})
        if len(usp) > 1:
            sw = []
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
        mep_res = execute_command(f"lspci -Dd {mep_vd}")
        if mep_res[5:12] in sw[0]:
            pass  # 第一个switch有mep,无需操作
        else:
            sw[0], sw[1] = sw[1], sw[0]  # 带mep的switch放到首位置
    # sw_bdf = [{'usp': xxx,
    # 'eps': [{'dsp': xxx,'ep': xxx,'driver': xxx,'name': xxx},{}...],
    # 'mep': {'dsp': xxx, 'ep': xxx, 'driver': xxx},
    # 'dma': [{'dsp': xxx, 'ep': xxx, 'driver': xxx},{}...],
    # 'ntb': {'dsp': xxx, 'ep': xxx, 'driver': xxx}, {}]
    all_sudu_sw = []
    mep_ep = mep_res[5:12]
    dma_ep_list = [dma_ep[5:12] for dma_ep in execute_command(f"lspci -Dd {dma_vd} |awk -F ' ' '{{print $1}}'").split()]
    ntb_ep_list = [ntb_ep[5:12] for ntb_ep in execute_command(f"lspci -Dd {ntb_vd} |awk -F ' ' '{{print $1}}'").split()]

    for partition in sw:
        mep_dict = {}  # 构建mep字典
        dma_arr = []  # 构建dma字典
        ntb_dict = {}  # 构建ntb字典
        ep_list = []  # 构建ep列表
        for bdf in partition[1:]:
            ep_bdf = []  # 多function考虑
            bus_text = execute_command(f"lspci -vs {bdf} |grep Bus")
            pattern = r'.*secondary=(.*),.*subordinate=(.*),.*'
            res = re.findall(pattern, bus_text)
            if not res:
                continue  # iep的情况
            secondary_bus, subordinate_bus = res[0]
            if secondary_bus == "00":
                continue
            elif secondary_bus == subordinate_bus:
                if execute_command(f"lspci -s {secondary_bus}:00.0"):
                    ep_bdf.append(secondary_bus + ":00.0")
                else:
                    continue  # dsp下无ep的情况
            else:
                ep_bdf = []
                multi_dev_count = int(subordinate_bus, 16) - int(secondary_bus, 16) + 1
                for j in range(multi_dev_count):
                    ep_bdf.append(f"{secondary_bus}:00.{j}")
            driver_res = execute_command(f"lspci -vvs {ep_bdf[0]} |grep 'driver in use' |awk -F ' ' '{{print $NF}}'")
            ep_vd = execute_command(f"lspci -ns {ep_bdf[0]} |awk -F ' ' '{{print $3}}'")
            for key, value in eps.items():
                if ep_vd == value:
                    name = key
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
            elif len(ep_bdf) == 1:
                ep_list.append({'dsp': bdf, 'ep': ep_bdf[0], 'driver': driver_res, 'name': name})
            else:
                for i in range(len(ep_bdf)):
                    ep_list.append({'dsp': bdf, 'ep': ep_bdf[i], 'driver': driver_res, 'name': name})
        all_sudu_sw.append({'usp': partition[0], 'eps': ep_list, 'mep': mep_dict, 'dma': dma_arr, 'ntb': ntb_dict})
        # assert len(ep_list) != 0, "Env check fail, Not Find EP!"
        if len(ep_list) == 0:
            print("Warning: Have a SW part not Find EP!")

    return all_sudu_sw


def get_speed(bdf):
    cap_speed = execute_command(
        f"lspci -vvs {bdf} |grep LnkCap: |grep -i Speed|awk -F ' ' '{{print$5}}' |awk -F ',' '{{print$1}}'")
    sta_speed = execute_command(f"lspci -vvs {bdf} |grep LnkSta: |grep -i Speed|awk -F ' ' '{{print$3}}'")
    return cap_speed, sta_speed


def get_width(bdf):
    cap_width = execute_command(
        f"lspci -vvs {bdf} |grep LnkCap: |grep -i Width|awk -F ' ' '{{print$7}}' |awk -F ',' '{{print$1}}'")
    sta_width = execute_command(f"lspci -vvs {bdf} |grep LnkSta: |grep -i Width|awk -F ' ' '{{print$6}}'")
    return cap_width, sta_width


def check_bar(bdf):
    bar = execute_command(f"lspci -vvs {bdf} |grep Region")
    if not bar:
        print(f"{bdf} BAR not found!")
    else:
        check_res = execute_command(f"lspci -vvs {bdf} |grep Region |egrep 'disabled|invalid'")
        if not check_res:
            return 0
        else:
            return 1


def check_aer(bdf):
    # RP && USP
    UESta = execute_command(f"lspci -vvs {bdf} |grep UESta").lstrip()
    res = UESta.split()
    for value in res:
        if value == "UESta:" or value.startswith("UnsupReq"):
            continue
        res = value[-1]
        if res == '+':
            print(f"{bdf} [AER UESta {value} Error]")
            return 1
        else:
            continue
    CESta = execute_command(f"lspci -vvs {bdf} |grep CESta").lstrip()
    res = CESta.split()
    for value in res:
        if value == "CESta:" or value.startswith("AdvNonFatalErr"):
            continue
        res = value[-1]
        if res == '+':
            print(f"{bdf} [AER CESta {value} Error]")
            return 1
        else:
            continue
    return 0


if __name__ == '__main__':
    all_sw = get_bdf()
    # print(all_sw)
    print(f"------------------------------预发布版本检查------------------------------\n")
    if all_sw:
        for idx, sw in enumerate(all_sw):
            usp_bdf = sw['usp']
            mep_dict = sw['mep']
            dma_arr = sw['dma']
            ntb_dict = sw['ntb']
            eps_arr = sw['eps']

            print(f"\033[1;35m------------------------------SW{idx}------------------------------\033[0m\n")
            print(f"\033[1;34m********************USP And USP Upstream Port AER Check**********\033[0m\n")
            # usp及usp上游port aer check
            usp_up_port = execute_command(
                f"lshw -class bridge -businfo |grep {usp_bdf} -B1 |head -n 1 |awk -F ' ' '{{print$1}}' |awk -F '@' '{{print$2}}'")
            usp_up_aer_res = check_aer(usp_up_port)
            if not usp_up_aer_res:
                print(f"\033[33mUsp's Upstream Port AER Check\033[0m: *** [\033[32mPASS\033[0m]")
            else:
                print(f"\033[33mUsp's Upstream Port AER Check\033[0m: *** [\033[31mFAIL\033[0m]")
            usp_aer_res = check_aer(usp_bdf)
            if not usp_aer_res:
                print(f"\033[33mUsp AER Check\033[0m: *** [\033[32mPASS\033[0m]\n")
            else:
                print(f"\033[33mUsp AER Check\033[0m: *** [\033[31mFAIL\033[0m]\n")

            # usp link speed and width check
            print(f"\033[1;34m********************USP Link Speed And Width Check********************\033[0m\n")
            print(f"\033[33mUSP\033[0m: {usp_bdf}")
            usp_info = execute_command(f"lspci -vvs {usp_bdf} |grep Lnk")
            print(f"{usp_bdf}\n{usp_info}\n")

            usp_cap_speed, usp_sta_speed = get_speed(usp_bdf)
            if usp_sta_speed == usp_cap_speed and usp_cap_speed:
                print(
                    f"\033[33mUsp Speed\033[0m: usp_cap_speed=usp_sta_speed={usp_sta_speed} *** [\033[32mPASS\033[0m]")
            else:
                print(
                    f"\033[33mUsp Speed\033[0m: usp_cap_speed={usp_cap_speed} usp_sta_speed={usp_sta_speed} *** [\033[31mFAIL\033[0m]")

            usp_cap_width, usp_sta_width = get_width(usp_bdf)
            if usp_sta_width == usp_cap_width and usp_cap_width:
                print(
                    f"\033[33mUsp Width\033[0m: usp_cap_width=usp_sta_width={usp_sta_width} *** [\033[32mPASS\033[0m]\n")
            else:
                print(
                    f"\033[33mUsp Width\033[0m: usp_cap_width={usp_cap_width} usp_sta_width={usp_sta_width} *** [\033[31mFAIL\033[0m]\n")
        for idx, sw in enumerate(all_sw):
            usp_bdf = sw['usp']
            mep_dict = sw['mep']
            dma_arr = sw['dma']
            ntb_dict = sw['ntb']
            eps_arr = sw['eps']
            print(f"\033[1;35m------------------------------SW{idx}------------------------------\033[0m\n")
            if mep_dict:
                print(f"\033[1;34m********************MEP iDSP Check********************\033[0m\n")
                print(f"mep_idsp={mep_dict['dsp']}")
                mep_idsp_info = execute_command(f"lspci -vvs {mep_dict['dsp']} |grep Lnk")
                print(f"{mep_dict['dsp']}\n{mep_idsp_info}\n")
                mep_idsp_cap_speed, mep_idsp_sta_speed = get_speed(mep_dict['dsp'])
                if mep_idsp_sta_speed == mep_idsp_cap_speed and mep_idsp_cap_speed:
                    print(
                        f"\033[33mMep iDSP Speed\033[0m: mep_idsp_cap_speed=mep_idsp_sta_speed={mep_idsp_sta_speed} *** [\033[32mPASS\033[0m]")
                else:
                    print(
                        f"\033[33mMep iDSP Speed\033[0m: mep_idsp_cap_speed={mep_idsp_cap_speed} mep_idsp_sta_speed={mep_idsp_sta_speed} *** [\033[31mFAIL\033[0m]")

                mep_idsp_cap_width, mep_idsp_sta_width = get_width(mep_dict['dsp'])
                if mep_idsp_sta_width == mep_idsp_cap_width and mep_idsp_cap_width:
                    print(
                        f"\033[33mMep iDSP Width\033[0m: mep_idsp_cap_width=mep_idsp_sta_width={mep_idsp_sta_width} *** [\033[32mPASS\033[0m]\n")
                else:
                    print(
                        f"\033[33mMep iDSP Width\033[0m: mep_idsp_cap_width={mep_idsp_cap_width} mep_idsp_sta_width={mep_idsp_sta_width} *** [\033[31mFAIL\033[0m]\n")
            else:
                print(f"This SW no MEP. May be is a partition!\n")

        for idx, sw in enumerate(all_sw):
            usp_bdf = sw['usp']
            mep_dict = sw['mep']
            dma_arr = sw['dma']
            ntb_dict = sw['ntb']
            eps_arr = sw['eps']
            print(f"\033[1;35m------------------------------SW{idx}------------------------------\033[0m\n")
            if mep_dict:
                print(f"\033[1;34m********************MEP iEP Check********************\033[0m\n")
                mep = mep_dict['ep']
                print(f"mep={mep}")
                mep_info = execute_command(f"lspci -vvs {mep} |grep Lnk")
                print(f"{mep}\n{mep_info}\n")
                mep_cap_speed, mep_sta_speed = get_speed(mep)
                if mep_sta_speed == mep_cap_speed and mep_cap_speed:
                    print(
                        f"\033[33mMep iEP Speed\033[0m: mep_cap_speed=mep_sta_speed={mep_sta_speed} *** [\033[32mPASS\033[0m]")
                else:
                    print(
                        f"\033[33mMep iEP Speed\033[0m: mep_cap_speed={mep_cap_speed} mep_sta_speed={mep_sta_speed} *** [\033[31mFAIL\033[0m]")
                mep_cap_width, mep_sta_width = get_width(mep)
                if mep_sta_width == mep_cap_width and mep_cap_width:
                    print(
                        f"\033[33mMep iEP Width\033[0m: mep_cap_width=mep_sta_width={mep_sta_width} *** [\033[32mPASS\033[0m]")
                else:
                    print(
                        f"\033[33mMep iEP Width\033[0m: mep_cap_width={mep_cap_width} mep_sta_width={mep_sta_width} *** [\033[31mFAIL\033[0m]")

                # mep driver check
                mep_driver = execute_command(f"lspci -k -s {mep} |grep use |grep nvme")
                if mep_driver:
                    print(f"\033[33mMep Driver\033[0m: mep_driver_in_use={mep_driver} *** [\033[32mPASS\033[0m]")
                else:
                    print(f"\033[33mMep Driver\033[0m: mep_driver_in_use={mep_driver} *** [\033[31mFAIL\033[0m]")

                # mep bar check
                res = check_bar(mep)
                if res == 0:
                    print(f"\033[33mMep BAR\033[0m: mep bar check *** [\033[32mPASS\033[0m]\n")
                else:
                    print(f"\033[33mMep BAR\033[0m: mep bar check *** [\033[31mFAIL\033[0m]\n")
            else:
                print(f"This SW no MEP. May be is a partition!\n")
        for idx, sw in enumerate(all_sw):
            usp_bdf = sw['usp']
            mep_dict = sw['mep']
            dma_arr = sw['dma']
            ntb_dict = sw['ntb']
            eps_arr = sw['eps']
            print(f"\033[1;35m------------------------------SW{idx}------------------------------\033[0m\n")

            if ntb_dict:
                print(f"\033[1;34m********************NTB iDSP Check********************\033[0m\n")
                print(f"ntb_idsp={ntb_dict['dsp']}")
                ntb_idsp_info = execute_command(f"lspci -vvs {ntb_dict['dsp']} |grep Lnk")
                print(f"{ntb_dict['dsp']}\n{ntb_idsp_info}\n")
                ntb_idsp_cap_speed, ntb_idsp_sta_speed = get_speed(ntb_dict['dsp'])
                if ntb_idsp_sta_speed == ntb_idsp_cap_speed and ntb_idsp_cap_speed:
                    print(
                        f"\033[33mNTB iDSP Speed\033[0m: ntb_idsp_cap_speed=ntb_idsp_sta_speed={ntb_idsp_sta_speed} *** [\033[32mPASS\033[0m]")
                else:
                    print(
                        f"\033[33mNTB iDSP Speed\033[0m: ntb_idsp_cap_speed={ntb_idsp_cap_speed} ntb_idsp_sta_speed={ntb_idsp_sta_speed} *** [\033[31mFAIL\033[0m]")
                ntb_idsp_cap_width, ntb_idsp_sta_width = get_width(ntb_dict['dsp'])
                if ntb_idsp_sta_width == ntb_idsp_cap_width and ntb_idsp_cap_width:
                    print(
                        f"\033[33mNTB iDSP Width\033[0m: ntb_idsp_cap_width=ntb_idsp_sta_width={ntb_idsp_sta_width} *** [\033[32mPASS\033[0m]\n")
                else:
                    print(
                        f"\033[33mNTB iDSP Width\033[0m: ntb_idsp_cap_width={ntb_idsp_cap_width} ntb_idsp_sta_width={ntb_idsp_sta_width} *** [\033[31mFAIL\033[0m]\n")
            else:
                print(f"This SW no NTB. May be is a base mode!\n")

        for idx, sw in enumerate(all_sw):
            usp_bdf = sw['usp']
            mep_dict = sw['mep']
            dma_arr = sw['dma']
            ntb_dict = sw['ntb']
            eps_arr = sw['eps']
            print(f"\033[1;35m------------------------------SW{idx}------------------------------\033[0m\n")

            if ntb_dict:
                print(f"\033[1;34m********************NTB iEP Check********************\033[0m\n")
                ntb = ntb_dict['ep']
                print(f"ntb={ntb}")
                ntb_info = execute_command(f"lspci -vvs {ntb} |grep Lnk")
                print(f"{ntb}\n{ntb_info}\n")
                ntb_cap_speed, ntb_sta_speed = get_speed(ntb)
                if ntb_sta_speed == ntb_cap_speed and ntb_cap_speed:
                    print(
                        f"\033[33mNTB iEP Speed\033[0m: ntb_cap_speed=ntb_sta_speed={ntb_sta_speed} *** [\033[32mPASS\033[0m]")
                else:
                    print(
                        f"\033[33mNTB iEP Speed\033[0m: ntb_cap_speed={ntb_cap_speed} ntb_sta_speed={ntb_sta_speed} *** [\033[31mFAIL\033[0m]")
                ntb_cap_width, ntb_sta_width = get_width(ntb)
                if ntb_sta_width == ntb_cap_width and ntb_cap_width:
                    print(
                        f"\033[33mNTB iEP Width\033[0m: ntb_cap_width=ntb_sta_width={ntb_sta_width} *** [\033[32mPASS\033[0m]\n")
                else:
                    print(
                        f"\033[33mNTB iEP Width\033[0m: ntb_cap_width={ntb_cap_width} ntb_sta_width={ntb_sta_width} *** [\033[31mFAIL\033[0m]\n")
            else:
                print(f"This SW no NTB. May be is a base mode!\n")
        for idx, sw in enumerate(all_sw):
            usp_bdf = sw['usp']
            mep_dict = sw['mep']
            dma_arr = sw['dma']
            ntb_dict = sw['ntb']
            eps_arr = sw['eps']
            print(f"\033[1;35m------------------------------SW{idx}------------------------------\033[0m\n")

            if dma_arr:
                print(f"\033[1;34m********************DMA iDSP Check********************\033[0m\n")
                for dma in dma_arr:
                    dma_idsp = dma['dsp']
                    print(f"dma_idsp={dma_idsp}")
                    dma_idsp_info = execute_command(f"lspci -vvs {dma_idsp} |grep Lnk")
                    print(f"{dma_idsp}\n{dma_idsp_info}\n")
                    dma_idsp_cap_speed, dma_idsp_sta_speed = get_speed(dma_idsp)
                    if dma_idsp_sta_speed == dma_idsp_cap_speed and dma_idsp_cap_speed:
                        print(
                            f"\033[33mDMA iDSP Speed\033[0m: dma_idsp_cap_speed=dma_idsp_sta_speed={dma_idsp_sta_speed} *** [\033[32mPASS\033[0m]")
                    else:
                        print(
                            f"\033[33mDMA iDSP Speed\033[0m: dma_idsp_cap_speed={dma_idsp_cap_speed} dma_idsp_sta_speed={dma_idsp_sta_speed} *** [\033[31mFAIL\033[0m]")
                    dma_idsp_cap_width, dma_idsp_sta_width = get_width(dma_idsp)
                    if dma_idsp_sta_width == dma_idsp_cap_width and dma_idsp_cap_width:
                        print(
                            f"\033[33mDMA iDSP Width\033[0m: dma_idsp_cap_width=dma_idsp_sta_width={dma_idsp_sta_width} *** [\033[32mPASS\033[0m]\n")
                    else:
                        print(
                            f"\033[33mDMA iDSP Width\033[0m: dma_idsp_cap_width={dma_idsp_cap_width} dma_idsp_sta_width={dma_idsp_sta_width} *** [\033[31mFAIL\033[0m]\n")
            else:
                print(f"This SW no DMA. May be cfg file is not set dma!\n")

        for idx, sw in enumerate(all_sw):
            usp_bdf = sw['usp']
            mep_dict = sw['mep']
            dma_arr = sw['dma']
            ntb_dict = sw['ntb']
            eps_arr = sw['eps']
            print(f"\033[1;35m------------------------------SW{idx}------------------------------\033[0m\n")

            if dma_arr:
                print(f"\033[1;34m********************DMA iEP Check********************\033[0m\n")
                for dma in dma_arr:
                    dma = dma['ep']
                    print(f"dma={dma}")
                    dma_info = execute_command(f"lspci -vvs {dma} |grep Lnk")
                    print(f"{dma}\n{dma_info}\n")
                    dma_cap_speed, dma_sta_speed = get_speed(dma)
                    if dma_sta_speed == dma_cap_speed and dma_cap_speed:
                        print(
                            f"\033[33mDMA iEP Speed\033[0m: dma_cap_speed=dma_sta_speed={dma_sta_speed} *** [\033[32mPASS\033[0m]")
                    else:
                        print(
                            f"\033[33mDMA iEP Speed\033[0m: dma_cap_speed={dma_cap_speed} dma_sta_speed={dma_sta_speed} *** [\033[31mFAIL\033[0m]")
                    dma_cap_width, dma_sta_width = get_width(dma)
                    if dma_sta_width == dma_cap_width and dma_cap_width:
                        print(
                            f"\033[33mDMA iEP Width\033[0m: dma_cap_width=dma_sta_width={dma_sta_width} *** [\033[32mPASS\033[0m]\n")
                    else:
                        print(
                            f"\033[33mDMA iEP Width\033[0m: dma_cap_width={dma_cap_width} dma_sta_width={dma_sta_width} *** [\033[31mFAIL\033[0m]\n")
            else:
                print(f"This SW no DMA. May be cfg file is not set dma!\n")
        for idx, sw in enumerate(all_sw):
            usp_bdf = sw['usp']
            mep_dict = sw['mep']
            dma_arr = sw['dma']
            ntb_dict = sw['ntb']
            eps_arr = sw['eps']
            print(f"\033[1;35m------------------------------SW{idx}------------------------------\033[0m\n")

            if eps_arr:
                print(f"\033[1;34m********************DSP With EP Check********************\033[0m\n")
                for ep in eps_arr:
                    dsp = ep['dsp']
                    print(f"dsp={dsp}")
                    dsp_info = execute_command(f"lspci -vvs {dsp} |grep Lnk")
                    print(f"{dsp}\n{dsp_info}\n")
                    dsp_cap_speed, dsp_sta_speed = get_speed(dsp)
                    if dsp_sta_speed == dsp_cap_speed and dsp_cap_speed:
                        print(
                            f"\033[33mDSP Speed\033[0m: dsp_cap_speed=dsp_sta_speed={dsp_sta_speed} *** [\033[32mPASS\033[0m]")
                    else:
                        print(
                            f"\033[33mDSP Speed\033[0m: dsp_cap_speed={dsp_cap_speed} dsp_sta_speed={dsp_sta_speed} *** [\033[31mFAIL\033[0m]")
                    dsp_cap_width, dsp_sta_width = get_width(dsp)
                    if dsp_sta_width == dsp_cap_width and dsp_cap_width:
                        print(
                            f"\033[33mDSP Width\033[0m: dsp_cap_width=dsp_sta_width={dsp_sta_width} *** [\033[32mPASS\033[0m]\n")
                    else:
                        print(
                            f"\033[33mDSP Width\033[0m: dsp_cap_width={dsp_cap_width} dsp_sta_width={dsp_sta_width} *** [\033[31mFAIL\033[0m]\n")
            else:
                print(f"This SW no EP. \n")

        for idx, sw in enumerate(all_sw):
            usp_bdf = sw['usp']
            mep_dict = sw['mep']
            dma_arr = sw['dma']
            ntb_dict = sw['ntb']
            eps_arr = sw['eps']
            print(f"\033[1;35m------------------------------SW{idx}------------------------------\033[0m\n")

            if eps_arr:
                print(f"\033[1;34m********************EP Check********************\033[0m\n")
                for ep in eps_arr:
                    ep_bdf = ep['ep']
                    print(f"ep={ep_bdf}")
                    ep_info = execute_command(f"lspci -vvs {ep_bdf} |grep Lnk")
                    print(f"{ep_bdf}\n{ep_info}\n")
                    ep_cap_speed, ep_sta_speed = get_speed(ep_bdf)
                    if ep_sta_speed == "2.5GT/s" and ep_cap_speed:
                        print(
                            f"\033[33mEP Speed\033[0m: ep_cap_speed={ep_cap_speed} ep_sta_speed={ep_sta_speed} *** [\033[32mPASS\033[0m]")
                    else:
                        print(
                            f"\033[33mEP Speed\033[0m: ep_cap_speed={ep_cap_speed} ep_sta_speed={ep_sta_speed} *** [\033[31mFAIL\033[0m]")
                    ep_cap_width, ep_sta_width = get_width(ep_bdf)
                    if ep_sta_width == "x4" and ep_cap_width:
                        print(
                            f"\033[33mEP Width\033[0m: ep_cap_width={ep_cap_width} ep_sta_width={ep_sta_width} *** [\033[32mPASS\033[0m]")
                    else:
                        print(
                            f"\033[33mEP Width\033[0m: ep_cap_width={ep_cap_width} ep_sta_width={ep_sta_width} *** [\033[31mFAIL\033[0m]")
                    # if ep_sta_speed == ep_cap_speed and ep_cap_speed:
                    #     print(f"\033[33mEP Speed\033[0m: ep_cap_speed={ep_cap_speed} ep_sta_speed={ep_sta_speed} *** [\033[32mPASS\033[0m]")
                    # else:
                    #     print(f"\033[33mEP Speed\033[0m: ep_cap_speed={ep_cap_speed} ep_sta_speed={ep_sta_speed} *** [\033[31mFAIL\033[0m]")
                    # ep_cap_width, ep_sta_width = get_width(ep_bdf)
                    # if ep_sta_width == ep_cap_width and ep_cap_width:
                    #     print(f"\033[33mEP Width\033[0m: ep_cap_width={ep_cap_width} ep_sta_width={ep_sta_width} *** [\033[32mPASS\033[0m]")
                    # else:
                    #     print(f"\033[33mEP Width\033[0m: ep_cap_width={ep_cap_width} ep_sta_width={ep_sta_width} *** [\033[31mFAIL\033[0m]")

                    # ep bar check
                    res = check_bar(ep_bdf)
                    if res == 0:
                        print(f"\033[33mEP BAR\033[0m: ep {ep_bdf} bar check *** [\033[32mPASS\033[0m]\n")
                    else:
                        print(f"\033[33mEP BAR\033[0m: ep {ep_bdf} bar check *** [\033[31mFAIL\033[0m]")
            else:
                print(f"This SW no EP. \n")
