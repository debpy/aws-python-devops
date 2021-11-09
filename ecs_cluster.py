import boto3
import sys
import time
from termcolor import colored
from defaultValues import get_default_values
from destroy_setup import destroy_ecs_cluster
from iam_role_and_sg import security_groups_checks, iam_role_creations
from loadbalancer import attach_target_with_lb


default_region_name = "ap-south-1"


ecs_client = boto3.client(service_name='ecs', region_name=default_region_name)
ec2_client = boto3.client(service_name="ec2", region_name=default_region_name)
sts_client = boto3.client(service_name="sts", region_name=default_region_name)


ecr_repository_name = "mcp_devops"
account_id = sts_client.get_caller_identity()['Account']
cluster_name = "MCP_ECS"
task_defination_name = "MCP_TD"
service_name = "MCP_SVC"
security_group_name= "MCP_SG"
ecs_iam_role_name = "MCP_ECS_Task_Execution_Role"
ecs_iam_managed_policyArn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
image_uri = f"{account_id}.dkr.ecr.{default_region_name}.amazonaws.com/{ecr_repository_name}:latest"
container_name = "nginx-web"
td_cpu = "256"
td_mem = "512"
container_cpu = 256
container_mem = 512
container_port = 80
host_port = 80


def task_definition():
    account_id = get_default_values()[0]
    td_response = ecs_client.register_task_definition(
        family=task_defination_name,
        taskRoleArn=f'arn:aws:iam::{account_id}:role/{ecs_iam_role_name}',
        executionRoleArn=f'arn:aws:iam::{account_id}:role/{ecs_iam_role_name}',
        networkMode='awsvpc',
        requiresCompatibilities=['FARGATE'],
        cpu=td_cpu,
        memory=td_mem,
        containerDefinitions=[
            {
                'name': container_name,
                'image': image_uri,
                'essential': True,
                'cpu': container_cpu,
                'memory': container_mem,
                'portMappings': [
                    {
                        'containerPort': container_port,
                        'hostPort': host_port,
                        'protocol': 'tcp'
                    }
                ]
            }
        ]
    )
    print(colored(f"Task Desfinition ({task_defination_name}) has been created", "green"))


def ecs_cluster():
    ecs_cluster_response = ecs_client.create_cluster(clusterName=cluster_name)
    return ecs_cluster_response
    
def ecs_service(sg_groupId, lb_tg_arn):
    ecs_client.create_service(
        cluster=cluster_name,
        serviceName=service_name,
        taskDefinition=task_defination_name,
        desiredCount=2,
        schedulingStrategy='REPLICA',
        launchType='FARGATE',
        deploymentConfiguration={
            'maximumPercent': 200,
            'minimumHealthyPercent': 100
        },
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': get_default_values()[1],
                'securityGroups': sg_groupId,
                'assignPublicIp': 'ENABLED'
            }
        },
        loadBalancers=[{
            'targetGroupArn': lb_tg_arn,
            'containerName': container_name,
            'containerPort': container_port
        }]
    )
    waiter = ecs_client.get_waiter('services_stable')
    waiter.wait(cluster=cluster_name,services=[service_name])
    print(colored(f"ECS Service ({service_name}) for the cluster ({cluster_name}) has been created", "green"))


def ecs_service_update():
    sg_groupId = []
    if not ec2_client.describe_security_groups(Filters=[{'Name':'group-name','Values': [security_group_name]}])['SecurityGroups']:
        print("Security Group is not available. Please create the Setup and then try the update")
        sys.exit(2)
    else:
        for each in ec2_client.describe_security_groups(Filters=[{'Name':'group-name','Values': [security_group_name]}])['SecurityGroups']:
            sg_groupId.append(each['GroupId'])
            response = ecs_client.update_service(
                cluster=cluster_name,
                service=service_name,
                desiredCount=2,
                taskDefinition=task_defination_name,
                deploymentConfiguration={
                    'deploymentCircuitBreaker': {
                        'enable': True,
                        'rollback': True
                    },
                    'maximumPercent': 200,
                    'minimumHealthyPercent': 100
                },
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': get_default_values()[1],
                        'securityGroups': sg_groupId,
                        'assignPublicIp': 'ENABLED'
                    }
                },
                forceNewDeployment=True
            )
            print(colored("ECS Service update request has been placed", "green"))


def launch_ecs_cluster():
    global sg_groupId
    get_default_values()
    iam_role_creations(ecs_iam_role_name,ecs_iam_managed_policyArn)
    sg_groupId = security_groups_checks()
    task_definition()
    ecs_cluster()
    dns_name = attach_target_with_lb(sg_groupId)
    ecs_service(sg_groupId, dns_name[2])
    print(colored("ECS Cluster and ALB Setup has been Created", "green"))
    print(colored(f"URL to Access the Webserver: {dns_name[1]}", "green"))

