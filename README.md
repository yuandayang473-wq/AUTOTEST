# AUTOTEST
执行方式
项目根目录下终端执行pytest '@tests_to_run.txt'

tests_to_run.txt文件用来配置执行测试用例的范围，内容示例如下：
tests/test_file.py                                 测试py文件下所有测试用例
tests/test_file.py::test_func1                     测试py文件下的test_func1测试用例
tests/test_file.py::TestClass                      测试py文件下的TestClass测试类下的所有测试用例
-m slow                                            执行标记为slow的测试用例
tests/                                             测试目录下的所有测试用例

循环执行测试脚本
例子：执行 10 次
for ($i = 1; $i -le 10; $i++) {
    Write-Host "第 $i 次执行"
    pytest '@tests_to_run.txt'
}