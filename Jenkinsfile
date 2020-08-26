node('docker-slave-cluster') {
    git branch: "develop", credentialsId: 'BBCREDENTIALS', url: "https://bitbucket.org/morrisonsplc/people-env-cloner"

    def config = readYaml file: './config/config.yml'
    def INPUT_PARAMS = input message: 'Please Provide Parameters', ok: 'Next',
                        parameters: [choice(name: 'from_environment', choices: config.env.keySet().join('\n'), description: 'Which environment do you want to clone from?'),
                                    choice(name: 'to_environment', choices: config.env.keySet().join('\n'), description: 'Which environment do you want to clone to?'),
                                    booleanParam(name: 'Lambda', defaultValue: true, description: 'Check to clone Lambdas'),
                                    booleanParam(name: 'Docker', defaultValue: true, description: 'Check to clone Docker Images'),
                                    booleanParam(name: 'DynamoDB', defaultValue: true, description: 'Check to clone DynamoDB tables')
                                    ]

    def from_env = INPUT_PARAMS.from_environment
    def to_env = INPUT_PARAMS.to_environment
    def source_image = null
    def target_image = null
    def source_image_tag = null
    def target_image_tag = null

    println(INPUT_PARAMS.Docker)

    if(from_env.equals(to_env)) {
        println("From and To environment cannot be same")
        return
    }
    else if(to_env in config["ro-env"]) {
        println("Cannot clone to read-only environment")
        return
    }

    def customImage = docker.build("jenkins")

    customImage.inside('-u root -v /var/run/docker.sock:/var/run/docker.sock') {
        stage('Preparing environment') {
            sh "make venv"
            sh "make init"
            sh "chmod 777 *"
        }

        stage('Cloning Docker Repositories') {
            if(INPUT_PARAMS.Docker == true) {
                config.docker.each { docker_repo ->
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: config.env[from_env]]]) {
                        def account_id = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        sh "set +x && \$(aws ecr get-login --region eu-west-1 --no-include-email)"
                        println("Cloning from ${docker_repo}")
                        source_image_tag = "${account_id}.dkr.ecr.eu-west-1.amazonaws.com/${docker_repo}:${from_env}"
                        source_image = docker.image(source_image_tag)
                        source_image.pull()
                    }
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: config.env[to_env]]]) {
                        def account_id = sh(script: "aws sts get-caller-identity --query Account --output text", returnStdout: true).trim()
                        sh "set +x && \$(aws ecr get-login --region eu-west-1 --no-include-email)"
                        println("Cloning to ${docker_repo}")
                        target_image_tag = "${account_id}.dkr.ecr.eu-west-1.amazonaws.com/${docker_repo}:${to_env}"
                        sh "docker tag ${source_image_tag} ${target_image_tag}"
                        target_image = docker.image(target_image_tag)
                        target_image.push()
                    }
                    println("Clean up for ${docker_repo}")
                    sh "docker rmi ${target_image_tag} ${source_image_tag}"
                }
            }
        }

        stage('Cloning AWS Lambda Functions') {
            if(INPUT_PARAMS.Lambda == true) {
                config.lambda.each { lambda ->
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: config.env[from_env]]]) {
                        println("Cloning Lambda ${lambda} from ${from_env}")
                        sh "make lambda args='pull ${lambda} ${from_env}'"
                        sh "ls -l"
                    }
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: config.env[to_env]]]) {
                        sh "make lambda args='push ${lambda} ${to_env} ${config.lambda_bucket[to_env]}'"
                        println("Cloning Lambda ${lambda} completed to ${to_env}")
                    }
                }
            }
        }

        stage('Cloning AWS DynamoDB') {
            if(INPUT_PARAMS.DynamoDB == true) {
                config.DynamoDB.each { table ->
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: config.env[from_env]]]) {
                        println("Cloning DynamoDB table ${table} from ${from_env}")
                        sh "make dynamo args='pull ${table} ${from_env}'"
                    }
                    withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: config.env[to_env]]]) {
                        sh "make dynamo args='push ${table} ${to_env}'"
                        println("Cloning dynamo ${table} completed to ${to_env}")
                    }
                }
            }
        }

        stage('Clean Up') {
            cleanWs()
            sh "rm -rf .venv"
        }
    }
}
