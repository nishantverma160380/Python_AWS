# People Environment Cloner #

This README would normally document whatever steps are necessary to get your application up and running.

### Overview: ###
Environment cloner clones AWS environment for project peacock. Following components are currently supported:
* Docker
* Lambda
* DynamoDB

### How do I clone? ###
[Jenkins Job](https://jenkins.p.morconnect.com/people/job/peacock-env-cloner) needs to be build. Appropriate input parameter once provided to the job will start the cloning.
Input parameters include:
* From environment
* To environment
* Checkboxes for components to be cloned


### Configuration ###

config.yml file in the repository contains all the necessay configurations. Configuration includes:
* List of Lambdas to be cloned ({ENV} will be replaced with environment name dynamically)
* List of Docker images to be cloned
* List of environments and corresponding Jenkins AWS credentials ID
* List of read only environments
