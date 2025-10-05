import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from stacks.network_stack import NetworkStack


def test_vpc_created():
    """VPCが作成されることを確認"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    template = Template.from_stack(stack)

    # VPCが作成されていることを確認
    template.resource_count_is("AWS::EC2::VPC", 1)

    # VPC CIDRブロックが正しいことを確認
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16"
    })


def test_subnets_created():
    """サブネットが正しく作成されることを確認"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    template = Template.from_stack(stack)

    # パブリックサブネットとプライベートサブネットが作成されていることを確認
    template.resource_count_is("AWS::EC2::Subnet", 4)


def test_nat_gateways_created():
    """NAT Gatewayが2つ作成されることを確認"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    template = Template.from_stack(stack)

    # NAT Gatewayが2つ作成されていることを確認
    template.resource_count_is("AWS::EC2::NatGateway", 2)


def test_security_groups_created():
    """セキュリティグループが正しく作成されることを確認"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    template = Template.from_stack(stack)

    # Lambda SGとAurora SGが作成されていることを確認
    template.resource_count_is("AWS::EC2::SecurityGroup", 2)


def test_tags_applied():
    """タグが正しく適用されることを確認"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    template = Template.from_stack(stack)

    # VPCにタグが適用されていることを確認
    template.has_resource_properties("AWS::EC2::VPC", {
        "Tags": Match.array_with([
            {"Key": "Env", "Value": "test"},
            {"Key": "Project", "Value": "bronzedraw"}
        ])
    })


def test_outputs_exported():
    """アウトプットが正しくエクスポートされることを確認"""
    app = cdk.App()
    stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    template = Template.from_stack(stack)

    # VpcId、LambdaSecurityGroupId、AuroraSecurityGroupIdがエクスポートされることを確認
    template.has_output("VpcId", {})
    template.has_output("LambdaSecurityGroupId", {})
    template.has_output("AuroraSecurityGroupId", {})
