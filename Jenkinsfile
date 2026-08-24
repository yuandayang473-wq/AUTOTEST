pipeline {
    agent any

    parameters {
        string(
            name: 'TEST_NAME',
            defaultValue: 'fio_read_test',
            description: 'Name of the test to run'
        )
    }

    stages {
        stage('Run Test') {
            steps {
                echo "Running test: ${params.TEST_NAME}"

                // 将参数作为环境变量传入，避免直接拼接到 shell 脚本。
                withEnv(["TEST_NAME=${params.TEST_NAME}"]) {
                    sh '''
                        set -eu
                        echo "Running test: $TEST_NAME"

                        # 在这里替换为真实测试命令，例如：
                        # ./run-test.sh "$TEST_NAME"
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