import json

import boto3.session
import pytest
from faker import Faker
from jobapi.config import env
from jobapi.libraries.aws.resources.asg import Asg
from jobapi.libraries.aws.resources.cdn import Cdn
from jobapi.libraries.aws.resources.cfn.changeset import Changeset
from jobapi.libraries.aws.resources.cfn.drift import Drift
from jobapi.libraries.aws.resources.cfn.stack import Stack
from jobapi.libraries.aws.resources.s3 import Bucket
from jobapi.models.runner import Attachment, Log, Payload
from jobapi.properties.aws.cfn import CfnUpdateProperties
from moto import mock_aws

# ----------------------- app


@pytest.fixture
def action_payload(faker) -> dict:
    return {
        "ticket": faker.port_number(),
        "username": faker.email(),
        "task": faker.uuid4(),
        "callback": f"{env.cmapi_endpoint}/{env.cmapi_version}/tasks/{faker.uuid4()}",
        "properties": {},
        "comment": faker.sentence(),
    }


@pytest.fixture
def app_payload_fixture(faker) -> Payload:
    return Payload(
        callback=faker.uri(),
        ticket=faker.random_int(1000, 8000),
        properties={
            "environment": "testlabor-project-test-eu-central-1",
            "task": faker.uuid4(),
        },
        username=faker.email(),
        comment=faker.sentence(),
    )


@pytest.fixture
def app_attachments_fixture(faker) -> list[Log]:
    attachments = []
    for i in range(faker.random_int(min=5, max=50)):
        attachments.append(
            Attachment(
                name=faker.file_name(),
                source=faker.sentence(),
            ),
        )
    return attachments


@pytest.fixture
def app_messages_fixture(faker) -> list[Log]:
    messages = []
    for i in range(faker.random_int(min=5, max=50)):
        messages.append(Log(message=faker.sentence()))
    return messages


@pytest.fixture
def app_aws_s3_fixture(aws_s3_client, faker) -> Bucket:
    return Bucket(client=aws_s3_client, name=faker.uuid4())


@pytest.fixture
def app_aws_cdn_fixture(aws_cdn_client, faker) -> Cdn:
    return Cdn(client=aws_cdn_client, distribution_id=faker.uuid4())


@pytest.fixture
def app_aws_asg_fixture(aws_asg_client, aws_mock_asg) -> Asg:
    return Asg(
        client=aws_asg_client,
        name=aws_mock_asg.get("AutoScalingGroupName"),
    )


@pytest.fixture
def app_aws_cfn_stack_fixture(aws_cfn_client, faker) -> Stack:
    return Stack(client=aws_cfn_client, name=faker.uuid4())


@pytest.fixture
def app_aws_cfn_changeset_fixture(aws_cfn_client, app_aws_cfn_stack_fixture, aws_mock_stack):
    stack = app_aws_cfn_stack_fixture
    return Changeset(
        client=aws_cfn_client,
        stack=stack.describe(),
        properties=CfnUpdateProperties(
            environment="testlabor-project-test-eu-central-1",
            stack_name=stack.name,
        ),
    )


@pytest.fixture
def app_aws_cfn_template_fixture_json(faker) -> str:
    return json.dumps(
        {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": app_aws_cfn_template_description("vpc"),
            "Parameters": {
                "EnableDnsSupportValue": {"Type": "Boolean", "Default": "true"},
                "HelloWorld": {"Type": "String", "Default": "WTF"},
            },
            "Resources": {
                "VPC": {
                    "Properties": {
                        "CidrBlock": f"{faker.ipv4()}/16",
                        "EnableDnsSupport": {"Ref": "EnableDnsSupportValue"},
                    },
                    "Type": "AWS::EC2::VPC",
                },
            },
        },
    )


def app_aws_cfn_template_description(template_type: str = None) -> str:
    faker = Faker()
    if template_type is None:
        template_type = faker.random_element(
            Drift.load_config_yaml("./jobapi/configs/cfn_upgrade.yml").keys(),
        )
    return f"### {faker.date()} ### {template_type} ### {{faker.sentence()}}"


# ----------------------- aws


@pytest.fixture
def aws_s3_client():
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def aws_r53_client():
    with mock_aws():
        yield boto3.client("route53", region_name="us-east-1")


@pytest.fixture
@mock_aws
def aws_mock_s3_bucket(aws_s3_client, app_aws_s3_fixture) -> dict:
    region = "us-east-1"
    boto3.resource("s3", region_name=region).create_bucket(
        Bucket=app_aws_s3_fixture.name,
    )


@pytest.fixture
def aws_cdn_client():
    with mock_aws():
        yield boto3.client("cloudfront", region_name="us-east-1")


@pytest.fixture
@mock_aws
def aws_mock_cdn(aws_cdn_client, faker) -> dict:
    return aws_cdn_client.create_distribution(
        DistributionConfig={
            "CallerReference": faker.uuid4(),
            "Origins": {
                "Quantity": 1,
                "Items": [
                    {
                        "Id": "origin1",
                        "DomainName": f"{faker.uuid4()}.s3.us-east-1.amazonaws.com",
                        "OriginPath": faker.file_path(),
                        "S3OriginConfig": {
                            "OriginAccessIdentity": "origin-access-identity/cloudfront/00000000000001",
                        },
                    },
                ],
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": "origin1",
                "ViewerProtocolPolicy": "allow-all",
                "MinTTL": 10,
                "ForwardedValues": {"QueryString": False, "Cookies": {"Forward": "none"}},
            },
            "Comment": faker.sentence(),
            "Enabled": False,
        },
    ).get("Distribution")


@pytest.fixture
def aws_ec2_client():
    with mock_aws():
        yield boto3.client("ec2", region_name="us-east-1")


@pytest.fixture
def aws_cfn_client():
    with mock_aws():
        yield boto3.client("cloudformation", region_name="us-east-1")


@pytest.fixture
def aws_asg_client():
    with mock_aws():
        yield boto3.client("autoscaling", region_name="us-east-1")


@pytest.fixture
@mock_aws
def aws_mock_asg(aws_asg_client, aws_mock_network, faker):
    client = aws_asg_client
    name = faker.uuid4()
    configName = faker.uuid4()
    client.create_launch_configuration(
        LaunchConfigurationName=configName,
        ImageId="ami-123",
        InstanceType="t2.medium",
    )
    client.create_auto_scaling_group(
        AutoScalingGroupName=name,
        MinSize=21,
        MaxSize=50,
        LaunchConfigurationName=configName,
        VPCZoneIdentifier=aws_mock_network["subnet1"],
    )
    return client.describe_auto_scaling_groups(AutoScalingGroupNames=[name])["AutoScalingGroups"][0]


@pytest.fixture
@mock_aws
def aws_mock_asg2(aws_asg_client, aws_mock_network, faker):
    client = aws_asg_client
    name = faker.uuid4()
    configName = faker.uuid4()
    client.create_launch_configuration(
        LaunchConfigurationName=configName,
        ImageId="ami-123",
        InstanceType="t2.micro",
    )
    client.create_auto_scaling_group(
        AutoScalingGroupName=name,
        MinSize=2,
        MaxSize=5,
        LaunchConfigurationName=configName,
        VPCZoneIdentifier=aws_mock_network["subnet1"],
    )
    return client.describe_auto_scaling_groups(AutoScalingGroupNames=[name])["AutoScalingGroups"][0]


@pytest.fixture
@mock_aws
def aws_mock_network():
    region_name = "us-east-1"
    ec2 = boto3.resource("ec2", region_name=region_name)
    vpc = ec2.create_vpc(CidrBlock="10.11.0.0/16")
    subnet1 = ec2.create_subnet(
        VpcId=vpc.id,
        CidrBlock="10.11.1.0/24",
        AvailabilityZone=f"{region_name}a",
    )
    subnet2 = ec2.create_subnet(
        VpcId=vpc.id,
        CidrBlock="10.11.2.0/24",
        AvailabilityZone=f"{region_name}b",
    )
    return {"vpc": vpc.id, "subnet1": subnet1.id, "subnet2": subnet2.id}


@pytest.fixture
@mock_aws
def aws_mock_ec2():
    client = boto3.client("ec2", region_name="us-east-1")
    reservation = client.run_instances(
        ImageId="ami-123",
        MinCount=1,
        MaxCount=1,
    )
    return reservation.get("Instances")[0]


@pytest.fixture
@mock_aws
def aws_mock_stack_template_url(faker):
    with mock_aws():
        region = "us-east-1"
        file = f"f{faker.uuid4()}.template"
        bucket = faker.uuid4()
        resource = boto3.resource("s3", region_name=region)
        resource.create_bucket(Bucket=bucket)
        resource.Object(bucket, file).put(
            Body=json.dumps(
                {
                    "AWSTemplateFormatVersion": "2010-09-09",
                    "Description": app_aws_cfn_template_description("s3-deploy-bucket"),
                    "Parameters": {
                        "MockupBucketName": {"Type": "String"},
                        "MockupDescription": {"Type": "String", "Default": "Mockup bucket name"},
                    },
                    "Resources": {
                        "Bucket": {
                            "Type": "AWS::S3::Bucket",
                            "Properties": {"BucketName": {"Ref": "MockupBucketName"}},
                        },
                    },
                },
            ),
        )
        s3 = boto3.client("s3", region_name=region)
        return s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": file},
        )


@pytest.fixture
@mock_aws
def aws_mock_changeset(
    aws_cfn_client,
    app_aws_cfn_changeset_fixture,
    aws_mock_stack,
    faker,
) -> Changeset:
    changeset = app_aws_cfn_changeset_fixture
    return aws_cfn_client.create_change_set(
        ChangeSetName=changeset.name,
        StackName=changeset.stack.get("StackName"),
        ChangeSetType="UPDATE",
        UsePreviousTemplate=True,
        Tags=[
            {"Key": faker.word(), "Value": faker.uuid4()},
        ],
        Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"],
    )


@pytest.fixture()
@mock_aws
def aws_mock_stack(app_aws_cfn_stack_fixture, aws_cfn_client, app_aws_cfn_template_fixture_json):
    stack_name = app_aws_cfn_stack_fixture.name
    aws_cfn_client.create_stack(
        StackName=stack_name,
        TemplateBody=app_aws_cfn_template_fixture_json,
    )
    return aws_cfn_client.describe_stacks(StackName=stack_name).get("Stacks")[0]


# ----------------------- custom aws mockups


@pytest.fixture()
def aws_mock_client_without_moto(faker):
    return boto3.client(
        "cloudformation",
        region_name="us-east-1",
        aws_access_key_id=faker.uuid4(),
        aws_secret_access_key=faker.uuid4(),
        aws_session_token=faker.uuid4(),
    )


# ----------------------- cmapi


@pytest.fixture
def cmapi_user_fixture(faker) -> dict:
    username = faker.email()
    return {
        "data": {
            "id": faker.unique.random_int(),
            "username": username,
            "email": username,
            "firstName": faker.first_name(),
            "lastName": faker.last_name(),
            "environments": [
                faker.word(),
                faker.word(),
                faker.word(),
            ],
            "updatedAt": str(faker.future_datetime()),
        },
    }
