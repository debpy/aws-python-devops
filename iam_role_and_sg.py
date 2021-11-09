import boto3
import json
import botocore
from botocore.exceptions import ClientError
from termcolor import colored
import time
from defaultValues import get_default_values
from destroy_setup import delete_load_balancer, delete_target_group, delete_ecs_service


default_region_name = "us-east-2"


iam_client = boto3.client(service_name='iam', region_name=default_region_name)
ec2_client = boto3.client(service_name="ec2", region_name=default_region_name)


security_group_name= "MCP_SG"


def security_group_creations():
    sg_groupId=[]
    sg_response = ec2_client.create_security_group(
        Description='This SG used for the ECS & ALB',
        GroupName=security_group_name,
        VpcId=get_default_values()[2]
    )
    ingress_response = ec2_client.authorize_security_group_ingress(
        GroupId=sg_response['GroupId'],
        IpPermissions=[
            {
                'FromPort': 80,
                'ToPort': 80,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ]
            }
        ]           
    )
    sg_groupId.append(sg_response['GroupId'])
    return sg_groupId


def security_groups_checks():
    if not ec2_client.describe_security_groups(Filters=[{'Name':'group-name','Values': [security_group_name]}])['SecurityGroups']:
        sg_groupId = security_group_creations()
        print(colored(f"Security Group ({security_group_name}) has been Created", "green"))
    else:
        delete_load_balancer()
        delete_target_group()
        delete_ecs_service()
        time.sleep(20)
        ec2_client.delete_security_group(GroupName=security_group_name)
        sg_groupId = security_group_creations()
        print(colored(f"Security Group ({security_group_name}) has been Updated", "green"))
    return sg_groupId


def iam_role_creations(role_name, policy_arn):
    assume_role_policy_document = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": [
                        "ecs.amazonaws.com",
                        "ecs-tasks.amazonaws.com"
                    ]
                },
                "Action": "sts:AssumeRole"
            }
        ]
    })
    try:
        role_creation = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=assume_role_policy_document,
            Tags=[
                {
                    'Key': 'CreatedBy',
                    'Value': 'MCPTeam'
                },
            ]
        )
        policy_attachment = iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
    except botocore.errorfactory.ClientError as error:
        if error.response['Error']['Code'] == 'EntityAlreadyExists':
            response = iam_client.update_role(RoleName=role_name)
            print(colored(f"IAM Role ({role_name}) has been Updated", "green"))
        else:
            raise error
