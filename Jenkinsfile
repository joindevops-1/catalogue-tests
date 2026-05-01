pipeline {
    agent {
        node {
            label 'roboshop'
        }
    }
    environment {
        SELENIUM_HUB   = "http://localhost:4444"
        NAMESPACE      = "roboshop"
        CONTAINER_NAME = "selenium-chrome-${BUILD_NUMBER}"
    }
    options {
        timeout(time: 15, unit: 'MINUTES')
    }
    stages {
        stage('Resolve URLs') {
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

                    def webIP = sh(
                        script: "kubectl get pod -l component=web -n ${NAMESPACE} -o jsonpath='{.items[0].status.podIP}'",
                        returnStdout: true
                    ).trim()

                    if (!webIP) {
                        error("No running web pod found in namespace '${NAMESPACE}'.")
                    }
                    env.APP_URL = "http://${webIP}"
                    echo "Web URL: ${env.APP_URL}"
                }
            }
        }

        stage('Start Selenium Container') {
            steps {
                sh """
                    docker rm -f ${CONTAINER_NAME} || true
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --network host \
                        --shm-size=2g \
                        selenium/standalone-chrome:latest
                """
                // Wait until the Selenium Grid is ready to accept sessions
                sh """
                    echo "Waiting for Selenium Grid to be ready..."
                    for i in \$(seq 1 20); do
                        if curl -sf http://localhost:4444/status | grep -q '"ready": *true'; then
                            echo "Selenium Grid is ready"
                            exit 0
                        fi
                        echo "Attempt \$i: not ready yet, retrying in 3s..."
                        sleep 3
                    done
                    echo "Selenium Grid did not become ready in time"
                    exit 1
                """
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
            // Stop and remove Selenium container regardless of test outcome
            sh "docker rm -f ${CONTAINER_NAME} || true"
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
