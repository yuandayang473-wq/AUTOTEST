pipeline {
    agent {label 'windows'}

    environment {
        TEST_NAME = 'high_low_temp_test'
    }

    stages {

        stage('Run Test') {
            steps {
                echo "Running test: ${env.TEST_NAME}"
            bat '''
                whoami
                echo SESSION=%SESSIONNAME%
                where py
                where python
                where python3
                py -3 -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"
                py -3 high_low_temp_ci.py
            '''
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: '*.log',
                allowEmptyArchive: true
            )
        }

        success {
            echo '构建成功'
        }

        failure {
            emailext(
                body: '${DEFAULT_CONTENT}',
                subject: '${DEFAULT_SUBJECT}',
                to: 'yuandayang@sudoinfotech.com',
                attachmentsPattern: '*.log'
            )
            echo '构建失败'
        }

        unstable {
            echo '构建不稳定'
        }
    }
}