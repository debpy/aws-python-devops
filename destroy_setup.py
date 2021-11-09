import boto3
from termcolor import colored
from botocore.exceptions import ClientError


default_region_name = "ap-south-1"


iam_client = boto3.client(service_name='iam', region_name=default_region_name)
ecs_client = boto3.client(service_name='ecs', region_name=default_region_name)
ec2_client = boto3.client(service_name="ec2", region_name=default_region_name)
elb_client = boto3.client(service_name="elbv2", region_name=default_region_name)
ecr_client = boto3.client(service_name='ecr', region_name=default_region_name)


cluster_name = "MCP_ECS"
task_defination_name = "MCP_TD"
ecs_iam_role_name = "MCP_ECS_Task_Execution_Role"
ecs_iam_managed_policyArn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
service_name = "MCP_SVC"
security_group_name= "MCP_SG"
lb_target_group = "MCP-TG-LB"
lb_name = "MCP-LB"
ecr_repository_name = "mcp_devops"


def delete_ecs_service():
    try:
        for each in ecs_client.describe_services(cluster=cluster_name,services=[service_name])['services']:
            if each['status']  == "INACTIVE":
                print(colored(f"Service ({service_name}) is not Active in the ECS Cluster ({cluster_name})", "blue"))             
            else:
                print(colored(f"Destroying the ECS Service ({service_name}) under the ECS Cluster ({cluster_name})", "yellow"))
                ecs_client.delete_service(cluster=cluster_name,service=service_name,force=True)
                waiter = ecs_client.get_waiter('services_inactive')
                waiter.wait(cluster=cluster_name,services=[service_name])
                print(colored(f"Destroyed the ECS Service ({service_name}) under the ECS Cluster ({cluster_name})", "green"))
    except Exception as e:
        if e.response['Error']['Code'] == "ClusterNotFoundException":
            print(colored(f"Service ({service_name}) is not Active in the ECS Cluster ({cluster_name})","blue"))
        else:
            print(colored("Please resolve this error and try again","red"))
            raise e


def delete_load_balancer():
    global listener_lb_arn
    try:
        for each in elb_client.describe_load_balancers(Names=[lb_name])['LoadBalancers']:
            if each['State']['Code'] == "active":
                print(colored(f"Destroying the ALB ({lb_name})", "yellow"))
                listener_lb_arn = each['LoadBalancerArn']
                for each in elb_client.describe_listeners(LoadBalancerArn=each['LoadBalancerArn'])['Listeners']:
                    elb_client.delete_listener(ListenerArn=each['ListenerArn'])
                print(colored(f"Destroyed the Listener of the ALB ({lb_name})", "green"))
                elb_client.delete_load_balancer(LoadBalancerArn=each['LoadBalancerArn'])
                waiter = elb_client.get_waiter('load_balancers_deleted')
                waiter.wait(LoadBalancerArns=[each['LoadBalancerArn']])
                print(colored(f"Destroyed the ALB ({lb_name})", "green"))
    except Exception as e:
        if e.response['Error']['Code'] == "LoadBalancerNotFound":
            print(colored(f"No ALB ({lb_name}) is Active","blue"))
        else:
            print(colored("Please resolve this error and try again","red"))
            raise e


def delete_target_group():
    try:
        for each in elb_client.describe_target_groups(Names=[lb_target_group])['TargetGroups']:
            if each['TargetGroupName'] == lb_target_group:
                print(colored(f"Destroying the Target Group ({lb_target_group})", "yellow"))
                elb_client.delete_target_group(TargetGroupArn=each['TargetGroupArn'])
                print(colored(f"Destroyed the Target Group ({lb_target_group})", "green"))
    except Exception as e:
        if e.response['Error']['Code'] == "TargetGroupNotFound":
            print(colored(f"No Target Group ({lb_target_group}) is Active","blue"))
        else:
            print(colored("Please resolve this error and try again","red"))
            raise e
 

def delete_ecs_cluster():
    for cluster in ecs_client.describe_clusters(clusters=[cluster_name])['clusters']:
        if cluster['status'] == "INACTIVE":
            print(colored(f"No ECS Cluster {cluster_name} is Active","blue"))
        elif cluster['status'] == "DRAINING":
            print(colored(f"ECS Cluster {cluster_name} is in Draining mode", "yellow"))
        else:
            print(colored(f"Destroying the ECS Cluster ({cluster_name})", "yellow"))
            ecs_client.delete_cluster(cluster=cluster_name)
            print(colored(f"Destroyed the ECS Cluster ({cluster_name})", "green"))


def delete_ecs_td():
    registered_task_definition_revisions = ecs_client.list_task_definitions(familyPrefix=task_defination_name)['taskDefinitionArns']
    print(colored(f"Destroying the ECS TaskDefinitions - ({task_defination_name})", "yellow"))
    for each in registered_task_definition_revisions:
        ecs_client.deregister_task_definition(taskDefinition=each)
    print(colored(f"Destroyed the ECS TaskDefinitions - ({task_defination_name})", "green"))


def delete_securitygroup():
    if ec2_client.describe_security_groups(Filters=[{'Name':'group-name','Values': [security_group_name]}])['SecurityGroups']:
        ec2_client.delete_security_group(GroupName=security_group_name)
        print(colored(f"Destroyed the Security Group - ({security_group_name})", "green"))
    else:
        print(colored(f"Security Group ({security_group_name}) doesn't exist","blue"))


def delete_iam_role():
    try:
        if iam_client.get_role(RoleName=ecs_iam_role_name)['Role']['RoleName'] == ecs_iam_role_name:
            iam_client.detach_role_policy(RoleName=ecs_iam_role_name,PolicyArn=ecs_iam_managed_policyArn)
            iam_client.delete_role(RoleName=ecs_iam_role_name)
    except Exception as e:
        if e.response['Error']['Code'] == "NoSuchEntity":
            print(colored(f"IAM Role ({ecs_iam_role_name}) doesn't exist","blue"))
        else:
            print(colored("Please resolve this error and try again","red"))
            print(e)


def destroy_ecr_repo():
    try: 
        repo_response = ecr_client.delete_repository(repositoryName=ecr_repository_name,force=True)
        repoArn = repo_response['repository']['repositoryArn']
        print(colored(f"Destroyed the ECR Repository - ({repoArn})", "green"))
    except Exception as e:
        if e.response['Error']['Code'] == "RepositoryNotFoundException":
            print(colored(f"ECR Repository ({ecr_repository_name}) doesn't exist","blue"))
        else:
            print(colored("Please resolve this error and try again","red"))
            print(e)

def destroy_ecs_cluster():
    delete_load_balancer()
    delete_target_group()
    delete_ecs_service()
    delete_ecs_cluster()
    delete_securitygroup()
    delete_iam_role()
    destroy_ecr_repo()
    print(colored("ECS Cluster and ALB Setup has been destroyed", "green"))
