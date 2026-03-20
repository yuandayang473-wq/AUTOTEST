import time
import traceback

import pytest
from Lib import *

# from Lib.logger import Logger
# LOGGER = Logger()


# 添加自定义命令行参数
def pytest_addoption(parser):
    """添加自定义命令行参数"""
    parser.addoption(
        "--aer-access-check",
        action="store",
        default="True",
        help="是否在测试前检查AER状态，有任何错误均不能测试，默认为True",
    )
    parser.addoption(
        "--uart-aer-check",
        action="store",
        default="True",
        help="是否在每个测试用例后检查uart AER状态，默认为True",
    )

# def pytest_exception_interact(node, call, report):
#     """
#     pytest 钩子函数，在测试发生异常时被调用。
#     """
#     if report.failed:
#         # 提取异常信息
#         exception_info = call.excinfo
#         error_message = f"测试失败: {node.nodeid}\n"
#         error_message += f"异常类型: {exception_info.type.__name__}\n"
#         error_message += f"异常信息: {exception_info.value}\n"
#
#         # 获取并格式化 traceback
#         tb = exception_info.tb
#         # 使用 pytest 的内建功能来获取更简洁、更易读的 traceback 字符串
#         tb_str = "".join(traceback.format_tb(tb))
#         error_message += f"Traceback:\n{tb_str}"
#
#         # 将格式化后的错误信息写入日志
#         LOGGER.error(error_message)

@pytest.fixture(scope="function", autouse=True)
def show_test_case(request):
    m = request.node.get_closest_marker("author")
    name = m.args[0] if m and m.args else "unknown"
    LOGGER.sys(f"开始测试用例{request.node.name}，用例作者：{name}".center(100, "-"))
    t1 =  time.time()
    yield
    t2 = time.time()
    time_use = round(t2 - t1)
    LOGGER.sys(f"用例{request.node.name}测试完成，总用时{time_use}s".center(100, "-"))

@pytest.fixture(scope="function", autouse=True)
def uart_aer_checker(request):
    yield
    if request.config.getoption("--uart-aer-check") == "True":
        config = CONFIG
        config.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
        ]
        with BASE.ssh_connect(uut=config.config["UUT"]):
            BASE.execute_run('python3 serial_check.py aer')


@pytest.fixture(scope="session", autouse=True)
def aer_access_checker(request):
    if request.config.getoption("--aer-access-check") == "True":
        config = CONFIG
        config.config = [
            {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
        ]
        with BASE.ssh_connect(uut=config.config["UUT"]):
            devices = METHOD.get_switch_info()
            for device in devices:
                assert "+" not in device.aer_status["CESta"], f"设备{device.device_bdf}存在Correctable Error"
                assert "+" not in device.aer_status["DevSta"], f"设备{device.device_bdf}存在Device Status Error"
                assert "+" not in device.aer_status["UESta"], f"设备{device.device_bdf}存在Uncorrectable Error"
    yield