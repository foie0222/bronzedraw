#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.network_stack import NetworkStack
from stacks.database_stack import DatabaseStack
from stacks.api_stack import ApiStack
from stacks.frontend_stack import FrontendStack

# 環境設定
ENV_NAME = os.getenv("ENV_NAME", "dev")  # dev, stg, prod
AWS_REGION = "ap-northeast-1"  # 東京リージョン

app = cdk.App()

# AWSアカウント/リージョン設定
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=AWS_REGION
)

# NetworkStack（VPC、サブネット、セキュリティグループ）
network_stack = NetworkStack(
    app,
    f"BronzedrawNetworkStack-{ENV_NAME}",
    env_name=ENV_NAME,
    env=env,
    description=f"Bronzedraw Network Stack for {ENV_NAME} environment",
)

# DatabaseStack（Aurora PostgreSQL Serverless v2）
database_stack = DatabaseStack(
    app,
    f"BronzedrawDatabaseStack-{ENV_NAME}",
    env_name=ENV_NAME,
    vpc=network_stack.vpc,
    aurora_sg=network_stack.aurora_sg,
    env=env,
    description=f"Bronzedraw Database Stack for {ENV_NAME} environment",
)
database_stack.add_dependency(network_stack)

# ApiStack（Lambda + API Gateway）
api_stack = ApiStack(
    app,
    f"BronzedrawApiStack-{ENV_NAME}",
    env_name=ENV_NAME,
    vpc=network_stack.vpc,
    lambda_sg=network_stack.lambda_sg,
    db_cluster=database_stack.db_cluster,
    db_secret=database_stack.db_secret,
    env=env,
    description=f"Bronzedraw API Stack for {ENV_NAME} environment",
)
api_stack.add_dependency(network_stack)
api_stack.add_dependency(database_stack)

# FrontendStack（S3 + CloudFront）
frontend_stack = FrontendStack(
    app,
    f"BronzedrawFrontendStack-{ENV_NAME}",
    env_name=ENV_NAME,
    api_url=api_stack.api.url,
    env=env,
    description=f"Bronzedraw Frontend Stack for {ENV_NAME} environment",
)
frontend_stack.add_dependency(api_stack)

app.synth()
