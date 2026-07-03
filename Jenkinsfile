def notifyDiscord(String status) {
    try {
        def credentialId = params.DISCORD_CREDENTIAL_ID?.trim()
        if (!credentialId) {
            echo '[discord] credential id is empty; notification skipped'
            return
        }
        withCredentials([string(credentialsId: credentialId, variable: 'DISCORD_WEBHOOK_URL')]) {
            if (isUnix()) {
                sh "python3 tools/notify_discord.py ${status} || true"
            } else {
                bat "python tools\\notify_discord.py ${status} || exit /b 0"
            }
        }
    } catch (err) {
        echo "[discord] notification skipped or failed without failing build: ${err.getMessage()}"
    }
}

pipeline {
    agent any

    triggers {
        githubPush()
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        booleanParam(name: 'OFFLINE_MODE', defaultValue: false, description: 'python.orgに接続せずfixtureで実行')
        string(name: 'DISCORD_CREDENTIAL_ID', defaultValue: 'discord-webhook-url', description: 'Jenkins Secret text credential id。空なら通知をスキップ')
    }

    environment {
        PYTHONUTF8 = '1'
        PYTHONIOENCODING = 'utf-8'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Tool versions') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 --version && node --version && git --version'
                    } else {
                        bat 'python --version && node --version && git --version'
                    }
                }
            }
        }
        stage('Unit tests') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 -m unittest discover -s tests -v'
                    } else {
                        bat 'python -m unittest discover -s tests -v'
                    }
                }
            }
        }
        stage('Scrape Python releases') {
            steps {
                script {
                    def offlineFlag = params.OFFLINE_MODE ? '--offline' : ''
                    if (isUnix()) {
                        sh "python3 scrape_releases.py ${offlineFlag}"
                    } else {
                        bat "python scrape_releases.py ${offlineFlag}"
                    }
                }
            }
        }
        stage('JavaScript dashboard') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'node tools/generate_dashboard.js output/releases.json output/index.html'
                    } else {
                        bat 'node tools\\generate_dashboard.js output\\releases.json output\\index.html'
                    }
                }
            }
        }
        stage('Verify outputs') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 tools/verify_outputs.py output'
                    } else {
                        bat 'python tools\\verify_outputs.py output'
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Archiving artifacts'
            archiveArtifacts artifacts: 'output/**', fingerprint: true, allowEmptyArchive: false
        }
        success {
            script {
                notifyDiscord('SUCCESS')
            }
        }
        failure {
            script {
                notifyDiscord('FAILURE')
            }
        }
    }
}

