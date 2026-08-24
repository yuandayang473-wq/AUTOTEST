pipeline {
    agent {
    label 'power'     // 指定带 power 标签的节点
}

    parameters {
        string(
            name: 'TEST_NAME',
            defaultValue: 'fio_read_test',
            description: 'Name of the test to run'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Run Test') {
            steps {
                echo "Running test: ${params.TEST_NAME}"

                sh """
                    echo "Running test: ${params.TEST_NAME}"
                """
            }
        }
    }

    post {
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