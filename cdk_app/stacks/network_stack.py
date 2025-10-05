from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    Tags,
)
from constructs import Construct


class NetworkStack(Stack):
    """
    VPC、サブネット、NAT Gateway、セキュリティグループを作成するスタック
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "dev", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name

        # VPC作成（dev環境: 10.0.0.0/16）
        self.vpc = ec2.Vpc(
            self,
            f"BronzedrawVpc-{env_name}",
            vpc_name=f"bronzedraw-vpc-{env_name}",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,  # 2つのAZを使用
            nat_gateways=2,  # 各AZにNAT Gateway配置（冗長化）
            subnet_configuration=[
                # パブリックサブネット（NAT Gateway配置用）
                ec2.SubnetConfiguration(
                    name=f"Public-{env_name}",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,  # 10.0.1.0/24, 10.0.2.0/24
                ),
                # プライベートサブネット（Lambda、Aurora配置用）
                ec2.SubnetConfiguration(
                    name=f"Private-{env_name}",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,  # 10.0.11.0/24, 10.0.12.0/24
                ),
            ],
        )

        # Lambda用セキュリティグループ
        self.lambda_sg = ec2.SecurityGroup(
            self,
            f"LambdaSg-{env_name}",
            vpc=self.vpc,
            security_group_name=f"bronzedraw-lambda-sg-{env_name}",
            description="Security group for Lambda functions",
            allow_all_outbound=True,
        )

        # Aurora用セキュリティグループ（後で使用）
        self.aurora_sg = ec2.SecurityGroup(
            self,
            f"AuroraSg-{env_name}",
            vpc=self.vpc,
            security_group_name=f"bronzedraw-aurora-sg-{env_name}",
            description="Security group for Aurora database",
            allow_all_outbound=False,
        )

        # Lambda SGからAurora SGへの5432ポート許可
        self.aurora_sg.add_ingress_rule(
            peer=self.lambda_sg,
            connection=ec2.Port.tcp(5432),
            description="Allow Lambda to access Aurora PostgreSQL",
        )

        # 全リソースにEnvタグを追加
        Tags.of(self).add("Env", env_name)
        Tags.of(self).add("Project", "bronzedraw")

        # Outputs
        CfnOutput(
            self,
            "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID",
            export_name=f"BronzedrawVpcId-{env_name}",
        )

        CfnOutput(
            self,
            "LambdaSecurityGroupId",
            value=self.lambda_sg.security_group_id,
            description="Lambda Security Group ID",
            export_name=f"BronzedrawLambdaSgId-{env_name}",
        )

        CfnOutput(
            self,
            "AuroraSecurityGroupId",
            value=self.aurora_sg.security_group_id,
            description="Aurora Security Group ID",
            export_name=f"BronzedrawAuroraSgId-{env_name}",
        )
