# !/usr/bin/python3
# -*- encoding: utf-8 -*-
'''
@Author  :   Harvey
@Software:   TestCase
@Time    :   2023/5/5
@Version :   1.0
@License :   Copyright ©LuxShare  2022 . All Rights Reserved.
@Desc    :   None
'''
import requests
import json
import re
import os

reports_path = os.path.dirname(os.path.abspath(os.path.split(os.path.realpath(__file__))[0]))
# reports_path = 
reports_path = reports_path + '/' + 'Config'


class MesSocket():
    def __init__(self):
        self.url = "http://172.20.0.99:9002/MainWebForm.aspx"

    def save_mes_info(self, rk_num):
        """
        发送post请求, 携带sn号需要手动输入
        并将返回数据保存到json文件中
        """
        payload = {"p": "GetAnconaInfo", "cmd": "ATT", "sn": rk_num}
        response = requests.post(self.url, json=payload)
        data = response.json()
        if data['Flag'] == 0:
            server_sn = data["Results"]["server_sn"]
            rk_part_number = data["Results"]["rk_part_number"]
            data["Results"]["rk_customer_part_number"]
            with open(f'{reports_path}/{server_sn}_mes.json', 'w', encoding='UTF-8') as f:
                f.write(json.dumps(data, indent=4, sort_keys=False) + '\n')
            return (rk_part_number, 200)
            
        else:
            return (data["ErrorMessage"], 404)

    def get_mes_info(self, server_sn):
        with open(f'{reports_path}/{server_sn}_mes.json', 'r', encoding='UTF-8') as f:
            output = eval(f.read())
            print(output)
        return output

    def json_filter(self, data, info):
        for line in data.split('\n'):
            if info in line:
                rst = line.split(':')[1].strip()
                return rst
            
    def get_hib_pn(self, sn):
        payload = {"p": "GetPNFromSN", "cmd": "ATT", "sn": sn}
        response = requests.post(self.url, json=payload)
        data = response.json()
        with open(f'{reports_path}/{sn}_mes.json', 'w', encoding='UTF-8') as f:
            f.write(json.dumps(data, indent=4, sort_keys=False) + '\n')
        return data
    
    def get_ubb_info(self, sn):
        payload = {"p": "GetOAMInfo", "cmd": "ATT", "sn": sn}
        response = requests.post(self.url, json=payload)
        data = response.json()
        with open(f'{reports_path}/{sn}_mes.json', 'w', encoding='UTF-8') as f:
            f.write(json.dumps(data, indent=4, sort_keys=False) + '\n')
        return data
    

    def upload_info(self, tdid, sn, mac):
        payload = {"cmd": "UPLOAD","server_tdid": tdid, "server_sn": sn, "server_mac": mac}
        response = requests.post(self.url, json=payload)
        data = response.json()
        return data
        

    def station_crossing(self, payload):
        """
        发送post请求, 携带sn号需要手动输入
        并将返回数据保存到json文件中
        """
        #pt = LXKS_K02-2FFATP-01_1_Pretest
        #rt = LXKS_K02-2FFATP-01_1_RT1
        #rt2 = LXKS_K02-2FFATP-01_1_RT2
        #ct = LXKS_K02-2FFATP-01_1_CT2
        #power = LXKS_K02-2FFATP-01_1_POWER

        response = requests.post(self.url, json=payload)
        data = response.json()
        if data['result']  != 'OK':
        # if data['Flag'] != 0:
            print(data)
            raise Exception("station_crossing is fail")

    def check_station_crossing(self, payload):
        response = requests.post(self.url, json=payload)
        data = response.json()
        print(data)
   
        

if __name__ == "__main__":
    mes = MesSocket()
    # mes.save_mes_info()
    mes.get_ubb_info("KS1408801036C3573")
