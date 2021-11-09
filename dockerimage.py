import boto3
import docker
import base64
from termcolor import colored


default_region_name = "us-east-2"


docker_client = docker.from_env(version='1.24')
ecr_client = boto3.client(service_name='ecr', region_name=default_region_name)
sts_client = boto3.client(service_name="sts", region_name=default_region_name)


repository_name = "mcp_devops"
account_id = sts_client.get_caller_identity()['Account']


def create_repository():
    try:
        for each in ecr_client.describe_repositories(registryId=account_id, repositoryNames=[repository_name])['repositories']:
            if each['repositoryName'] == repository_name:
                print(colored(f"ECR Repository ({repository_name}) Already Exists", "blue"))
                repo_uri = each['repositoryUri']
    except Exception as e:
        if e.response['Error']['Code'] == "RepositoryNotFoundException":
            ecr_response = ecr_client.create_repository(
                repositoryName=repository_name,
                tags=[
                    {
                        'Key': 'CreatedBy',
                        'Value': 'MCPTeam'
                    },
                ]
            )
        repo_uri = ecr_response['repository']['repositoryUri']
    return repo_uri


def ecr_repo_login():
    repo_uri =create_repository()
    token = ecr_client.get_authorization_token()
    username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
    registry = token['authorizationData'][0]['proxyEndpoint']
    docker_client.login(username, password, registry=registry)
    return repo_uri 


def docker_image_build():
    repository_url = ecr_repo_login()
   # build = docker_client.images.build(path="/home/ec2-user/microcredentials/mcp/dockerimage/", tag=repository_url)
    build = docker_client.images.build(path="/root/SkillUp/aws-python-devops", tag=repository_url)
    print(colored(f"Successfully Created the Docker image ({build[0]})", "green"))
    return repository_url


def docker_image_push():
    image_name = docker_image_build()
    for each in docker_client.images.push(image_name, stream=True, decode=True):
       print(each)

