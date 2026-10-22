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
                credentialsId: 'scratch2devops',
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


       
       stage('Deploy') {
           steps {
               withCredentials([
                   string(
                        credentialsId: 'employee-db-password',
                        variable: 'DB_PASSWORD'
                   ),
                   usernamePassword(
                       credentialsId: 'scratch2devops',
                       usernameVariable: 'DOCKERHUB_USERNAME',
                       passwordVariable: 'DOCKERHUB_TOKEN'
                   )
                ]) {
                   sh '''
                      set -e
                      trap 'docker logout >/dev/null 2>&1 || true' EXIT

                     PREVIOUS_IMAGE=$(docker inspect employee_api \
                         --format '{{.Config.Image}}')

                     echo "Currently deployed image: $PREVIOUS_IMAGE"
                     echo "New image to deploy: $DOCKERHUB_USERNAME/employee-operations-platform:$BUILD_NUMBER"
                     export IMAGE_TAG="$BUILD_NUMBER"

                     echo "$DOCKERHUB_TOKEN" | docker login \
                    --username "$DOCKERHUB_USERNAME" \
                    --password-stdin

                    docker compose -p employee-operations-platform pull api

                    docker compose -p employee-operations-platform up -d --no-deps api
                  
                    echo "Waiting for employee_api to become healthy..."
                    
                    healthy=false

                    for attempt in $(seq 1 12); do
                        health=$(docker inspect employee_api \
                           --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}')

                        echo "Health check attempt $attempt/12: $health"

                        if [ "$health" = "healthy" ]; then
                            echo "Deployment health check passed!"
                            healthy=true
                            break
                        fi

                        if [ "$health" = "unhealthy" ] || [ "$health" = "no-healthcheck" ]; then
                              echo "ERROR: Container is $health"
                              exit 1
                        fi

                        sleep 5
                   done
                   
                        

                   echo "Testing deployed API..."

                   response=$(curl --fail --silent --show-error \
                       --max-time 10 \
                      http://api:8000/health)

                   echo "API response: $response"

                   echo "$response" | grep -q '"status":"healthy"'

                  echo "Post-deployment API test passed!"
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
