import boto3
from termcolor import colored
from defaultValues import get_default_values
from iam_role_and_sg import *


default_region_name = "us-east-2"


elb_client = boto3.client(service_name="elbv2", region_name=default_region_name)


lb_target_group = "MCP-TG-LB"
lb_name = "MCP-LB"


def loadbalancer(sg_groupId):
    try: 
        for each in elb_client.describe_load_balancers(Names=[lb_name])['LoadBalancers']:
            if (each['state']['code'] == "active") or (each['state']['code'] == "provisioning"):
                lb_arn = each['LoadBalancerArn']
                dns_name = each['DNSName']
                print(colored(f"Load Balancer ({lb_name}) is already exists", "blue"))
    except Exception as e:
        if e.response['Error']['Code'] == "LoadBalancerNotFound":
            lb_response = elb_client.create_load_balancer(
                Name=lb_name,
                Subnets=get_default_values()[1],
                SecurityGroups=sg_groupId,
                Scheme='internet-facing',
                Tags=[
                    {
                        'Key': 'CreatedBy',
                        'Value': 'MCPTeam'
                    },
                ],
                Type='application',
                IpAddressType='ipv4'
            )
            for each in lb_response['LoadBalancers']:
                lb_arn = each['LoadBalancerArn']
                dns_name = each['DNSName']
            waiter = elb_client.get_waiter('load_balancer_available')
            waiter.wait(Names=[lb_name])
            print(colored(f"Load Balancer ({lb_name}) has been created", "green"))
        else:
            print(colored("Please resolve this error and try again", "red"))
            raise e
    return lb_arn, dns_name


def loadbalancer_target_group():
    try:
        for each in elb_client.describe_target_groups(Names=[lb_target_group])['TargetGroups']:
            if each['TargetGroupName'] == lb_target_group:
                print(colored(f"Target Group ({lb_target_group}) is already exists", "blue"))
                tg_arn = each['TargetGroupArn']
    except Exception as e:
        if e.response['Error']['Code'] == "TargetGroupNotFound":
                tg_response = elb_client.create_target_group(
                    Name=lb_target_group,
                    Protocol='HTTP',
                    ProtocolVersion='HTTP1',
                    Port=80,
                    VpcId=get_default_values()[2],
                    HealthCheckProtocol='HTTP',
                    HealthCheckPort='traffic-port',
                    HealthCheckEnabled=True,
                    HealthCheckPath='/',
                    HealthCheckIntervalSeconds=30,
                    HealthCheckTimeoutSeconds=5,
                    HealthyThresholdCount=5,
                    UnhealthyThresholdCount=2,
                    Matcher={
                        'HttpCode': '200'
                    }, 
                    TargetType='ip',
                    Tags=[
                        {
                            'Key': 'CreatedBy',
                            'Value': 'MCPTeam'
                        },
                    ]
                )
                for each in tg_response['TargetGroups']:
                    tg_arn = each['TargetGroupArn']
                print(colored(f"Target Group ({lb_target_group}) has been created", "green"))
        else:
            print(colored("Please resolve this error and try again", "red"))
            raise e
    return tg_arn


def attach_target_with_lb(sg_groupId):
    lb_runner = loadbalancer(sg_groupId)
    tg_arn = loadbalancer_target_group()
    lb_arn =lb_runner[0]
    dns_name = lb_runner[1]
    try: 
        for each in elb_client.describe_listeners(LoadBalancerArn=lb_arn)['Listeners']:
            if each['LoadBalancerArn'] == lb_arn:
                print(colored(f"Listeners is already exists for the ALB ({lb_name})", "blue"))
    except Exception as e:
        raise e
    else:
        response = elb_client.create_listener(
            LoadBalancerArn=lb_arn,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': tg_arn,
                }
            ],
            Tags=[
                {
                    'Key': 'CreatedBy',
                    'Value': 'MCPTeam'
                },
            ]
        )
        print(colored(f"Listener for the ALB ({lb_name}) has been created", "green"))
        return lb_arn, dns_name, tg_arn
