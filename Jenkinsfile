pipeline {
    agent {label 'windows'}

    options {
        skipDefaultCheckout(true)
    }

    environment {
        TEST_NAME = 'high_low_temp_test'
    }

    stages {
        stage('Prepare Workspace') {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage('Run Test') {
            steps {
                echo "Running test: ${env.TEST_NAME}"
                bat '''
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

        cleanup {
            deleteDir()
        }
    }
}