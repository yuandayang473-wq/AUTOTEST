pipeline {
    agent any

    parameters {
        choice(
            name: 'TEST_NAME',
            choices: [
                'fio_read_test',
                'fio_write_test',
                'fio_randread_test',
                'fio_randwrite_test'
            ],
            description: '选择要执行的 fio 测试'
        )

        string(
            name: 'FIO_TEST_FILE',
            defaultValue: '',
            description: '可选：fio 测试文件的绝对路径；为空时使用 Jenkins Workspace'
        )
    }

    stages {
        stage('Prepare') {
            steps {
                checkout scm

                sh '''
                    set -eu
                    chmod +x scripts_run-test.sh
                    command -v fio
                    command -v zip
                '''
            }
        }

        stage('Run Test') {
            steps {
                echo "Running test: ${params.TEST_NAME}"

                // 参数通过环境变量传递，脚本内还会校验 TEST_NAME 白名单。
                withEnv([
                    "TEST_NAME=${params.TEST_NAME}",
                    "FIO_TEST_FILE=${params.FIO_TEST_FILE}"
                ]) {
                    sh '''
                        set -eu
                        ./script_run-test.sh "$TEST_NAME"
                    '''
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'target/surefire-reports/*.xml'

            archiveArtifacts(
                artifacts: '*_testlog.zip',
                allowEmptyArchive: true
            )

            emailext(
                body: '${DEFAULT_CONTENT}',
                subject: '${DEFAULT_SUBJECT}',
                to: 'yuandayang@sudoinfotech.com',
                attachmentsPattern: '*_testlog.zip'
            )
        }

        success {
            echo '构建成功'
        }

        failure {
            echo '构建失败'
        }

        unstable {
            echo '构建不稳定'
        }
    }
}