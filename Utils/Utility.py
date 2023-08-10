import time
import datetime
import os
import contextlib
# import platform, socket, re, uuid, json, psutil
import logging

from Utils.Login import SshConnect


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


def os_env(server_cnf, local_cnf, log):
    # 测试否是在os 环境下
    server_ip = server_cnf.get("os_ip")
    with SshConnect(
            ip=local_cnf["os_ip"],
            user=local_cnf["os_user"],
            password=local_cnf["os_pwd"],
            logger=log,
            login_retry=1,
    ) as ssh:
        parser = ssh.run(
            "ping -c 1 {ip}".format(ip=server_ip), retry_expt=1, i_exit_code=True
        ).str_parser()
        log.info(
            "SSH Execute command ok, Output below: \n%s" % parser.get_origin_data()
        )
        val = parser.get_value(r"(100% packet loss)")
        if val == "Null":
            return True
        return False


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


def creat_logger_files(case, cycle):
    l_name = list(os.path.split(case.logger.log_name))
    time_tag = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
    l_name[-1] = f"{case.__class__.__name__}_{cycle}-{time_tag}.log"

    fh = logging.FileHandler(os.path.join(*l_name))  # for file out
    fh.setFormatter(case.parent.logger_factory.fmt)

    p_logger = case.parent.get_logger()
    p_logger.removeHandler(case.parent.logger_factory.fh)

    for handler in case.logger.handlers[:]:  # make a copy of the list
        case.logger.removeHandler(handler)

    case.logger.addHandler(fh)


# def getSystemInfo():
#     try:
#         info = {}
#         info["OS"] = platform.system()
#         info["Kernel"] = platform.release()
#         info["architecture"] = platform.machine()
#         info["hostname"] = socket.gethostname()
#         info["ip-address"] = socket.gethostbyname(socket.gethostname())
#         info["mac-address"] = ":".join(re.findall("..", "%012x" % uuid.getnode()))
#         info["processor"] = platform.processor()
#         info["ram"] = str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB"
#         return json.dumps(
#             info,
#             indent=4,
#             separators=(
#                 ",",
#                 ": ",
#             ),
#         )
#     except Exception as e:
#         logging.exception(e)


def create_logger(name):
    logger = logging.getLogger(name)
    # 创建一个handler，用于写入日志文件
    filename = f'{name}.log'
    fh = logging.FileHandler(filename, mode='w+', encoding='utf-8')
    # 再创建一个handler用于输出到控制台
    ch = logging.StreamHandler()
    # 定义输出格式(可以定义多个输出格式例formatter1，formatter2)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    # 定义日志输出层级
    logger.setLevel(logging.DEBUG)
    # 定义控制台输出层级
    # logger.setLevel(logging.DEBUG)
    # 为文件操作符绑定格式（可以绑定多种格式例fh.setFormatter(formatter2)）
    fh.setFormatter(formatter)
    # 为控制台操作符绑定格式（可以绑定多种格式例ch.setFormatter(formatter2)）
    ch.setFormatter(formatter)
    # 给logger对象绑定文件操作符
    logger.addHandler(fh)
    # 给logger对象绑定文件操作符
    return logger


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