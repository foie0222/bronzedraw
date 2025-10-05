from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    Tags,
)
from constructs import Construct


class ApiStack(Stack):
    """
    Lambda + API Gateway でバックエンドAPIを構築するスタック
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str = "dev",
        vpc: ec2.Vpc = None,
        lambda_sg: ec2.SecurityGroup = None,
        db_cluster: rds.DatabaseCluster = None,
        db_secret: secretsmanager.Secret = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name

        # API Gateway CloudWatch Logs用のロール
        apigw_cloudwatch_role = iam.Role(
            self,
            f"ApiGatewayCloudWatchRole-{env_name}",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonAPIGatewayPushToCloudWatchLogs"
                ),
            ],
        )

        # API Gateway アカウント設定（CloudWatch Logsロール）
        apigw.CfnAccount(
            self,
            f"ApiGatewayAccount-{env_name}",
            cloud_watch_role_arn=apigw_cloudwatch_role.role_arn,
        )

        # Lambda実行ロール
        lambda_role = iam.Role(
            self,
            f"LambdaExecutionRole-{env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Secrets Managerからシークレット読み取り権限を付与
        if db_secret:
            db_secret.grant_read(lambda_role)

        # Lambda関数（FastAPI + Mangum）
        from aws_cdk import BundlingOptions

        self.jan_api_lambda = _lambda.Function(
            self,
            f"JanApiLambda-{env_name}",
            function_name=f"bronzedraw-jan-api-{env_name}",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_asset(
                "../backend",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            handler="app.main.handler",  # Mangum handler
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "ENV": env_name,
                "DB_SECRET_ARN": db_secret.secret_arn if db_secret else "",
                "DB_CLUSTER_ENDPOINT": db_cluster.cluster_endpoint.hostname if db_cluster else "",
                "DB_NAME": "bronzedraw",
            },
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[lambda_sg] if lambda_sg else None,
            # LogGroupはLambdaが自動作成（警告は無視）
        )

        # API Gateway（REST API）
        self.api = apigw.LambdaRestApi(
            self,
            f"JanApi-{env_name}",
            rest_api_name=f"bronzedraw-jan-api-{env_name}",
            handler=self.jan_api_lambda,
            proxy=True,  # /{proxy+} ですべてのリクエストをLambdaに転送
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,  # 本番環境では特定オリジンに制限
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["*"],
            ),
            deploy_options=apigw.StageOptions(
                stage_name=env_name,
                throttling_rate_limit=1000,  # リクエスト/秒
                throttling_burst_limit=2000,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
            ),
        )

        # タグ追加
        Tags.of(self).add("Env", env_name)
        Tags.of(self).add("Project", "bronzedraw")

        # Outputs
        CfnOutput(
            self,
            "ApiUrl",
            value=self.api.url,
            description="API Gateway URL",
            export_name=f"BronzedrawApiUrl-{env_name}",
        )

        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=self.jan_api_lambda.function_arn,
            description="Lambda Function ARN",
            export_name=f"BronzedrawLambdaArn-{env_name}",
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=self.jan_api_lambda.function_name,
            description="Lambda Function Name",
            export_name=f"BronzedrawLambdaName-{env_name}",
        )
