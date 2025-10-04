#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.network_stack import NetworkStack
from stacks.frontend_stack import FrontendStack
from stacks.api_stack import ApiStack

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
    f"SilverloseNetworkStack-{ENV_NAME}",
    env_name=ENV_NAME,
    env=env,
    description=f"Silverlose Network Stack for {ENV_NAME} environment",
)

# ApiStack（Lambda + API Gateway）
api_stack = ApiStack(
    app,
    f"SilverloseApiStack-{ENV_NAME}",
    env_name=ENV_NAME,
    vpc=network_stack.vpc,
    lambda_sg=network_stack.lambda_sg,
    env=env,
    description=f"Silverlose API Stack for {ENV_NAME} environment",
)
api_stack.add_dependency(network_stack)

# FrontendStack（S3 + CloudFront）
frontend_stack = FrontendStack(
    app,
    f"SilverloseFrontendStack-{ENV_NAME}",
    env_name=ENV_NAME,
    api_url=api_stack.api.url,
    env=env,
    description=f"Silverlose Frontend Stack for {ENV_NAME} environment",
)
frontend_stack.add_dependency(api_stack)

app.synth()
