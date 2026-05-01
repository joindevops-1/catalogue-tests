pipeline {
    agent {
        node {
            label 'roboshop'
        }
    }
    environment {
        NAMESPACE = "roboshop"
    }
    options {
        timeout(time: 15, unit: 'MINUTES')
    }
    stages {
        stage('Resolve Catalogue URL') {
            steps {
                script {
                    def podIP = sh(
                        script: "kubectl get pod -l component=catalogue -n ${NAMESPACE} -o jsonpath='{.items[0].status.podIP}'",
                        returnStdout: true
                    ).trim()

                    if (!podIP) {
                        error("No running catalogue pod found in namespace '${NAMESPACE}'.")
                    }
                    env.CATALOGUE_URL = "http://${podIP}:8080"
                    echo "Catalogue URL: ${env.CATALOGUE_URL}"
                }
            }
        }

        stage('Install Python Dependencies') {
            steps {
                sh 'pip3 install -r requirements.txt --quiet'
            }
        }

        stage('Run Catalogue Tests') {
            steps {
                sh """
                    pytest tests/ \
                        -v \
                        --html=report.html \
                        --self-contained-html \
                        --junitxml=junit-report.xml \
                        -p no:warnings
                """
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'report.html', allowEmptyArchive: true
            junit allowEmptyResults: true, testResults: 'junit-report.xml'
            cleanWs()
        }
        success {
            echo "All catalogue tests passed."
        }
        failure {
            echo "One or more catalogue tests failed — check the HTML report above."
        }
    }
}
