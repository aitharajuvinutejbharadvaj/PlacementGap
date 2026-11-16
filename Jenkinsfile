pipeline {
  agent any

  options {
    timestamps()
    timeout(time: 35, unit: 'MINUTES')
    disableConcurrentBuilds()
    skipDefaultCheckout(true)
  }

  environment {
    COMPOSE_PROJECT_NAME = "placementgap-ci-${BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Check Docker runner') {
      steps {
        script {
          if (isUnix()) {
            sh 'docker version'
            sh 'docker compose version'
          } else {
            bat 'docker version'
            bat 'docker compose version'
          }
        }
      }
    }

    stage('Build and run backend tests') {
      steps {
        dir('Placement Gap') {
          script {
            if (isUnix()) {
              sh 'docker compose -f docker-compose.ci.yml build app e2e'
              sh 'docker compose -f docker-compose.ci.yml run --rm --no-deps e2e ruff check agent api ontology tests e2e'
              sh 'docker compose -f docker-compose.ci.yml run --rm --no-deps e2e python -m pytest -q tests --junitxml=/app/artifacts/selenium/backend-junit.xml'
            } else {
              bat 'docker compose -f docker-compose.ci.yml build app e2e'
              bat 'docker compose -f docker-compose.ci.yml run --rm --no-deps e2e ruff check agent api ontology tests e2e'
              bat 'docker compose -f docker-compose.ci.yml run --rm --no-deps e2e python -m pytest -q tests --junitxml=/app/artifacts/selenium/backend-junit.xml'
            }
          }
        }
      }
    }

    stage('Run Selenium browser tests') {
      steps {
        dir('Placement Gap') {
          script {
            if (isUnix()) {
              sh 'docker compose -f docker-compose.ci.yml up --build --abort-on-container-exit --exit-code-from e2e e2e'
            } else {
              bat 'docker compose -f docker-compose.ci.yml up --build --abort-on-container-exit --exit-code-from e2e e2e'
            }
          }
        }
      }
    }
  }

  post {
    always {
      dir('Placement Gap') {
        script {
          if (isUnix()) {
            sh 'docker compose -f docker-compose.ci.yml down --volumes --remove-orphans || true'
          } else {
            bat 'docker compose -f docker-compose.ci.yml down --volumes --remove-orphans || exit /b 0'
          }
        }
      }
      junit allowEmptyResults: true, testResults: 'Placement Gap/artifacts/selenium/*.xml'
      archiveArtifacts allowEmptyArchive: true, artifacts: 'Placement Gap/artifacts/selenium/*.png,Placement Gap/artifacts/selenium/*.xml'
    }
  }
}
