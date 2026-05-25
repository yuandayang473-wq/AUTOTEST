import time
import traceback

import pytest
from Lib import *
import os

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



PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


def _format_duration(seconds: float) -> str:
    """将秒数格式化为更易读的时长字符串。"""
    total = int(round(seconds))
    days, rem = divmod(total, 24 * 3600)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def _compact_tb(excinfo):
    """只保留项目内栈帧，过滤 pytest/pluggy 框架噪音。"""
    tb = excinfo.tb
    frames = []
    while tb is not None:
        frame = tb.tb_frame
        lineno = tb.tb_lineno
        code = frame.f_code
        filename = os.path.abspath(code.co_filename)

        # 仅保留工作区内的代码帧
        if filename.startswith(PROJECT_ROOT):
            frames.append((filename, lineno, code.co_name))
        tb = tb.tb_next

    if frames:
        lines = []
        for f, ln, fn in frames:
            lines.append(f'  File "{f}", line {ln}, in {fn}')
        lines.append(f"{excinfo.type.__name__}: {excinfo.value}")
        return "\n".join(lines)

    # 如果没有项目内帧，兜底输出最后几帧，避免信息丢失
    full = traceback.extract_tb(excinfo.tb)
    tail = full[-3:] if len(full) > 3 else full
    lines = traceback.format_list(tail)
    lines.append(f"{excinfo.type.__name__}: {excinfo.value}\n")
    return "".join(lines).rstrip()


def _build_phase_failure_block(phase, nodeid, excinfo, report):
    if excinfo is None:
        return "\n".join(
            [
                f"测试失败[{phase}]: {nodeid}",
                f"异常信息: {getattr(report, 'longreprtext', '未知错误')}",
            ]
        )

    return "\n".join(
        [
            f"测试失败[{phase}]: {nodeid}",
            f"异常类型: {excinfo.type.__name__}",
            f"异常信息: {excinfo.value}",
            "Traceback:",
            _compact_tb(excinfo),
        ]
    )


def _log_failure_block_file_only(block: str):
    t = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
    with open(LOGGER.log_name, "a", encoding="utf-8") as f:
        for row in block.split("\n"):
            f.write(f"{t}\tERROR\t{row}\n")


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if not report.failed:
        return

    phase = report.when
    block = _build_phase_failure_block(phase, item.nodeid, call.excinfo, report)
    # 失败详情仅写日志文件，避免控制台在 TeamCity 节点间交叉重排
    _log_failure_block_file_only(block)

@pytest.fixture(scope="function", autouse=True)
def show_test_case(request):
    m = request.node.get_closest_marker("author")
    name = m.args[0] if m and m.args else "unknown"
    LOGGER.sys(f"开始测试用例{request.node.name}，用例作者：{name}".center(100, "-"))
    t1 = time.time()
    yield
    t2 = time.time()
    time_use = _format_duration(t2 - t1)
    LOGGER.sys(f"用例{request.node.name}测试完成，总用时{time_use}".center(100, "-"))

@pytest.fixture(scope="function", autouse=True)
def uart_aer_checker(request, show_test_case):
    LOGGER.info("uart_aer_checker start")
    yield
    LOGGER.info("uart_aer_checker end")
    # if request.config.getoption("--uart-aer-check") == "True":
    #     config = CONFIG
    #     config.config = [
    #         {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
    #     ]
    #     with BASE.ssh_connect(uut=config.config["UUT"]):
    #         BASE.execute_run('python3 serial_check.py aer')


# @pytest.fixture(scope="session", autouse=True)
# def aer_access_checker(request):
#     if request.config.getoption("--aer-access-check") == "True":
#         config = CONFIG
#         config.config = [
#             {"file": "Device.yaml", "name": "UUT", "key": "UUT_01"},
#         ]
#         with BASE.ssh_connect(uut=config.config["UUT"]):
#             devices = METHOD.get_switch_info()
#             for device in devices:
#                 assert "+" not in device.aer_status["CESta"], f"设备{device.device_bdf}存在Correctable Error"
#                 assert "+" not in device.aer_status["DevSta"], f"设备{device.device_bdf}存在Device Status Error"
#                 assert "+" not in device.aer_status["UESta"], f"设备{device.device_bdf}存在Uncorrectable Error"
#     yield

