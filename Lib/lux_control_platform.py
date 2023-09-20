import base64
import os
import time
import json

from .Config import JsonLoadConfig
from .lux_http import RequestFile, Requests
from .Utility import get_file_content
from .Constant import ErrCode


class ControlPlatform:

    def __init__(self, case):
        self.case = case
        self._tcs_server_api = None

    def run(self, cmd: str):
        self.case.get_logger().info("SSH Execute command: %s" % cmd)
        self.case.need_exec_cmd = cmd

    def _gen_platform_api(self):
        cfg = JsonLoadConfig(cfg_path_name="", cfg_name="jobcontext.json").get_config()
        tcs_server_api = cfg["flowdata"]["tcs_server_api"].strip()
        self._tcs_server_api = tcs_server_api

    def put_platform_data(self, value: dict, key="lux_tcs_info"):
        if not isinstance(value, dict):
            raise TypeError(f"{value} is must dict type")

        if not self._tcs_server_api:
            self._gen_platform_api()

        json_name = "register_platform.json"
        value = base64.b64encode(json.dumps(value).encode("utf-8"))
        data = {
            key: value.decode("utf-8")
        }
        JsonLoadConfig(cfg_path_name="", cfg_name=json_name).dump_config(data, is_new_file=True)
        abs_json = os.path.join(self.case.root_path, json_name)
        # self.case.get_logger().info(f"{self._tcs_server_api} 24 {abs_json}")
        parser = self.case.os_run.run(f"{self._tcs_server_api} 24 {abs_json}")
        if parser.check_field(r"cpu_chk=fail"):
            self.case.fail(ErrCode.INIT_PARAMS, "register jobcontent error")

    def get_platform_data(self, key="lux_tcs_info"):
        if not self._tcs_server_api:
            self._gen_platform_api()

        str_data = JsonLoadConfig(cfg_path_name="", cfg_name="jobcontext.json").data(f"unitData.propertyMap.{key}")
        b64_data = bytes(str_data, encoding="utf-8")
        data = base64.b64decode(b64_data)
        return json.loads(data)

    def getFileContent(self, name, path="."):
        return get_file_content(os.path.join(path, name))

    def check_uut(self, action="on"):
        """
        检查 uut 状态
        :param action: on/off , on 检查开机状态, off, 关机状态
        :return:
        """
        rf = RequestFile(logger=self.case.get_logger())
        tcs_flow_log = "tcsflow.log"
        rf.remove_file_by_name(tcs_flow_log)
        uut_ip = JsonLoadConfig(cfg_path_name="", cfg_name="jobcontext.json").data("unitData.propertyMap.target")
        flow_url = "http://{0}:9080/work/tcsflow.log".format(uut_ip)
        logger = self.case.get_logger()
        ret = rf.wget(flow_url)
        msg = "check_uut by get uut flow log: ret={0}, flow_url:{1}, action={2}".format(ret, flow_url, action)
        logger.info(msg)
        wait_time = 60
        curr_time = 0
        b_ready = False
        if action == "on":  # check uut ready
            # ======= need wait while uut listen =====
            max_time = 17 * 60
            logger.info("wait uut poweron timout {0}s.".format(max_time))
            while not b_ready and curr_time < max_time:  # 1000s +1=17mins
                if ret == 0:
                    flow_log = self.getFileContent(tcs_flow_log)
                    if "step 3 ===tcp listen port" in flow_log:  # uut start listen is power on ok.
                        b_ready = True
                        break

                stu_statu = "check uut power {0}, wait {1}s.".format(action, wait_time)
                logger.info(stu_statu)

                self.case.sleep(60)

                rf.remove_file_by_name(tcs_flow_log)

                ret = rf.wget(flow_url)
                msg = "ret={0}, wget flow_url={1}".format(ret, flow_url)
                logger.info(msg)
                curr_time += wait_time

            if b_ready:
                msg = " uut poweron finish. flow listen ready."
                logger.info(msg)
            else:
                msg = " uut poweron fail. please check power box config and uut status!"
                logger.info(msg)

        elif action == "off":  # check uut poweroff.
            # ======= need wait while uut can not connect =====
            max_time = 5 * 60
            message = ""
            while not b_ready and curr_time < max_time:  # 4+1=5mins
                if ret != 0:
                    message = "check off ok, return 0."
                    logger.info(message)
                    b_ready = True
                    break
                else:
                    rf.remove_file_by_name(tcs_flow_log)
                stu_statu = "check uut power {0}, wait {1}s.".format(action, curr_time)
                logger.info(stu_statu)

                time.sleep(60)
                ret = rf.wget(flow_url)
                message = "ret={0}, flow_url wget={1}".format(ret, flow_url)
                logger.info(message)
                curr_time += wait_time

            if b_ready:
                msg = "{0} uut poweroff finish.".format(message)
            else:
                msg = "uut poweroff fail, please check power box config! \r\n{0}".format(message)
            logger.info(msg)
        return b_ready

    def get_pdu_info(self):
        pdu_api = JsonLoadConfig(cfg_path_name="", cfg_name="jobcontext.json").data(f"flowdata.tcs_locationservice_url")
        res = Requests.get(pdu_api)
        devices = res["device"]

        pdu_data = {
            'ip_address': "",
            'head_port': "",
            'pdu_model': '',
        }

        for device in devices:
            if device["DEVICETYPE"] == "PDU":
                pdu_data["ip_address"] = device["DEVICEIP"]
                device["MIBNODE"] = "19,20~1.3.6.1.4.1.23273.3.1.1.6~8,10,12,14,16,18"
                pdu_port_info = device["MIBNODE"].strip()
                if not pdu_port_info:
                    self.case.fail(ErrCode.INIT_PARAMS, "please configuration pdu info")

                prots = pdu_port_info.split("~")

                if len(prots) > 3:
                    self.case.fail(ErrCode.INIT_PARAMS, "please configuration pdu info")

                if len(prots) == 3:
                    pdu_data["head_port"] = " ".join(prots[0].split(","))
                    pdu_data["tail_port"] = " ".join(prots[2].split(","))
                    pdu_data["pdu_model"] = prots[1]
                else:
                    pdu_data["port"] = " ".join(prots[0].split(","))
                    pdu_data["pdu_model"] = prots[1]
                break
        else:
            self.case.fail(ErrCode.INIT_PARAMS, "please configuration pdu info")

        return pdu_data
