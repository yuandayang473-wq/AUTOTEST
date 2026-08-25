#!/usr/bin/env bash
# 执行 fio 测试，并生成 Jenkins JUnit 报告和日志压缩包。

set -uo pipefail

TEST_NAME="${1:-${TEST_NAME:-fio_read_test}}"
REPORT_DIR="target/surefire-reports"
LOG_DIR="testlogs/${TEST_NAME}"
LOG_FILE="${LOG_DIR}/fio.log"
ZIP_FILE="${TEST_NAME}_testlog.zip"

mkdir -p "$REPORT_DIR" "$LOG_DIR"

if ! saaa >/dev/null 2>&1; then
    echo "错误：未找到 fio 命令，请在 Jenkins Agent 上安装 fio。" | tee "$LOG_FILE"
    cat > "${REPORT_DIR}/fio-test.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="fio" tests="1" failures="1" errors="0" skipped="0">
  <testcase classname="fio" name="${TEST_NAME}">
    <failure message="fio command not found">请在 Jenkins Agent 上安装 fio。</failure>
  </testcase>
</testsuite>
EOF
    zip -rq "$ZIP_FILE" "$LOG_DIR" 2>/dev/null || true
    exit 1
fi

# 根据测试名称选择固定参数；不要将用户输入直接拼接为 fio 参数。
case "$TEST_NAME" in
    fio_read_test)
        FIO_ARGS=(
            --name=fio_read_test
            --rw=read
            --bs=4k
            --size=1G
            --runtime=60
            --time_based
            --iodepth=16
            --direct=1
            --numjobs=1
            --group_reporting
        )
        ;;
    fio_write_test)
        FIO_ARGS=(
            --name=fio_write_test
            --rw=write
            --bs=4k
            --size=1G
            --runtime=60
            --time_based
            --iodepth=16
            --direct=1
            --numjobs=1
            --group_reporting
        )
        ;;
    fio_randread_test)
        FIO_ARGS=(
            --name=fio_randread_test
            --rw=randread
            --bs=4k
            --size=1G
            --runtime=60
            --time_based
            --iodepth=16
            --direct=1
            --numjobs=1
            --group_reporting
        )
        ;;
    fio_randwrite_test)
        FIO_ARGS=(
            --name=fio_randwrite_test
            --rw=randwrite
            --bs=4k
            --size=1G
            --runtime=60
            --time_based
            --iodepth=16
            --direct=1
            --numjobs=1
            --group_reporting
        )
        ;;
    *)
        echo "错误：不支持的 TEST_NAME：${TEST_NAME}" | tee "$LOG_FILE"
        echo "支持的值：fio_read_test、fio_write_test、fio_randread_test、fio_randwrite_test" | tee -a "$LOG_FILE"

        cat > "${REPORT_DIR}/fio-test.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="fio" tests="1" failures="1" errors="0" skipped="0">
  <testcase classname="fio" name="${TEST_NAME}">
    <failure message="Unsupported TEST_NAME">支持的值：fio_read_test、fio_write_test、fio_randread_test、fio_randwrite_test</failure>
  </testcase>
</testsuite>
EOF
        zip -rq "$ZIP_FILE" "$LOG_DIR" 2>/dev/null || true
        exit 1
        ;;
esac

# 可以通过 Jenkins 环境变量 FIO_TEST_FILE 指定测试文件位置。
# 默认文件位于 workspace 中，适合临时测试；生产环境建议指定独立磁盘挂载点。
TEST_FILE="${FIO_TEST_FILE:-${WORKSPACE:-$PWD}/fio-test.data}"

echo "开始执行测试：${TEST_NAME}" | tee "$LOG_FILE"
echo "测试文件：${TEST_FILE}" | tee -a "$LOG_FILE"
echo "执行命令：fio ${FIO_ARGS[*]} --filename=${TEST_FILE}" | tee -a "$LOG_FILE"

start_time="$(date +%s)"
set +e
fio "${FIO_ARGS[@]}" --filename="$TEST_FILE" 2>&1 | tee -a "$LOG_FILE"
fio_status=${PIPESTATUS[0]}
set -e
end_time="$(date +%s)"
duration=$((end_time - start_time))

if [[ "$fio_status" -eq 0 ]]; then
    cat > "${REPORT_DIR}/fio-test.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="fio" tests="1" failures="0" errors="0" skipped="0" time="${duration}">
  <testcase classname="fio" name="${TEST_NAME}" time="${duration}"/>
</testsuite>
EOF
    echo "测试成功。" | tee -a "$LOG_FILE"
else
    cat > "${REPORT_DIR}/fio-test.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="fio" tests="1" failures="1" errors="0" skipped="0" time="${duration}">
  <testcase classname="fio" name="${TEST_NAME}" time="${duration}">
    <failure message="fio exited with status ${fio_status}">详细日志请查看归档文件 ${ZIP_FILE}。</failure>
  </testcase>
</testsuite>
EOF
    echo "测试失败，fio 返回码：${fio_status}" | tee -a "$LOG_FILE"
fi

# fio 可能会保留测试数据；成功或失败后均尽量清理。
rm -f "$TEST_FILE"

# 即使 zip 工具不存在，也不能覆盖原本的 fio 执行结果。
if command -v zip >/dev/null 2>&1; then
    rm -f "$ZIP_FILE"
    zip -rq "$ZIP_FILE" "$LOG_DIR"
else
    echo "警告：未安装 zip，无法生成 ${ZIP_FILE}" | tee -a "$LOG_FILE"
fi

exit "$fio_status"