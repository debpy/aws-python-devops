import boto3

default_region_name = "ap-south-1"

sts_client = boto3.client(service_name="sts", region_name=default_region_name)
ec2_client = boto3.client(service_name="ec2", region_name=default_region_name)


def get_default_values():
    subnet_ids = []
    account_id = sts_client.get_caller_identity()['Account']
    vpc_id = ec2_client.describe_vpcs(Filters=[{'Name': 'is-default','Values': ['true']}])
    for each in vpc_id['Vpcs']:
        default_vpc_id = each['VpcId']
    subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id','Values': [default_vpc_id]}])
    for each in subnets['Subnets']:
        subnet_ids.append(each['SubnetId'])
    return account_id, subnet_ids, default_vpc_id
