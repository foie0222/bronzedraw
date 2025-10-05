from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    SecretValue,
    CfnOutput,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    Tags,
)
from constructs import Construct


class DatabaseStack(Stack):
    """
    Aurora PostgreSQL Serverless v2 を作成するスタック
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "dev",
        vpc: ec2.Vpc = None,
        aurora_sg: ec2.SecurityGroup = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name

        # データベース認証情報をSecrets Managerに保存
        self.db_secret = secretsmanager.Secret(
            self,
            f"AuroraSecret-{env_name}",
            secret_name=f"bronzedraw-aurora-{env_name}",
            description=f"Aurora PostgreSQL credentials for {env_name}",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username":"bronzedraw"}',
                generate_string_key="password",
                exclude_punctuation=True,
                password_length=32,
            ),
        )

        # Aurora PostgreSQL Serverless v2 クラスター
        self.db_cluster = rds.DatabaseCluster(
            self,
            f"AuroraCluster-{env_name}",
            cluster_identifier=f"bronzedraw-aurora-{env_name}",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_16_6
            ),
            credentials=rds.Credentials.from_secret(self.db_secret),
            default_database_name="bronzedraw",
            writer=rds.ClusterInstance.serverless_v2(
                f"Writer-{env_name}",
                enable_performance_insights=True,
                performance_insight_retention=rds.PerformanceInsightRetention.DEFAULT,  # 7日間
            ),
            serverless_v2_min_capacity=0.5,  # 最小ACU
            serverless_v2_max_capacity=1.0,  # 最大ACU
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[aurora_sg] if aurora_sg else None,
            backup=rds.BackupProps(
                retention=Duration.days(7 if env_name == "prod" else 1),
                preferred_window="17:00-18:00",  # JST 02:00-03:00
            ),
            preferred_maintenance_window="Sun:18:00-Sun:19:00",  # JST 日曜 03:00-04:00
            cloudwatch_logs_exports=["postgresql"],  # CloudWatch Logsにログ出力
            removal_policy=RemovalPolicy.SNAPSHOT if env_name == "prod" else RemovalPolicy.DESTROY,
            deletion_protection=True if env_name == "prod" else False,
            enable_data_api=True,  # RDS Query Editor用にData APIを有効化
        )

        # タグ追加
        Tags.of(self).add("Env", env_name)
        Tags.of(self).add("Project", "bronzedraw")

        # Outputs
        CfnOutput(
            self,
            "DBClusterEndpoint",
            value=self.db_cluster.cluster_endpoint.hostname,
            description="Aurora Cluster Endpoint",
            export_name=f"BronzedrawDBClusterEndpoint-{env_name}",
        )

        CfnOutput(
            self,
            "DBClusterIdentifier",
            value=self.db_cluster.cluster_identifier,
            description="Aurora Cluster Identifier",
            export_name=f"BronzedrawDBClusterIdentifier-{env_name}",
        )

        CfnOutput(
            self,
            "DBSecretArn",
            value=self.db_secret.secret_arn,
            description="Database Secret ARN",
            export_name=f"BronzedrawDBSecretArn-{env_name}",
        )

        CfnOutput(
            self,
            "DBName",
            value="bronzedraw",
            description="Database Name",
            export_name=f"BronzedrawDBName-{env_name}",
        )
