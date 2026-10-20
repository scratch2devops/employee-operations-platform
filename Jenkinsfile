pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Environment Check') {
            steps {
                sh 'python3 --version'
                sh 'git --version'
            }
        }

        stage('Create Virtual Environment') {
            steps {
                sh 'python3 -m venv .venv'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '.venv/bin/python -m pip install -r requirements-dev.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh '.venv/bin/python -m pytest -v tests/'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t employee-operations-platform:${BUILD_NUMBER} .'
            }
        }
       
        
        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                credentialsId: 'dockerhub-creds',
                usernameVariable: 'DOCKERHUB_USERNAME',
                passwordVariable: 'DOCKERHUB_TOKEN'
              )]) {
                  sh '''
                      echo "$DOCKERHUB_TOKEN" | docker login \
                         --username "$DOCKERHUB_USERNAME" \
                         --password-stdin

                      docker tag employee-operations-platform:${BUILD_NUMBER} \
                          "$DOCKERHUB_USERNAME/employee-operations-platform:${BUILD_NUMBER}"

                      docker push \
                          "$DOCKERHUB_USERNAME/employee-operations-platform:${BUILD_NUMBER}"

                      docker logout
                   '''
              }
          } 
       }
 
    }

    post {
        success {
            echo 'CI pipeline completed successfully!'
        }
        failure {
            echo 'CI pipeline failed. Check the console output.'
        }
        always {
            echo 'CI pipeline execution finished.'
        }
    }
}
