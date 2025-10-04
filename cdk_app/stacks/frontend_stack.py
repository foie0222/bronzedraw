from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    Tags,
    CustomResource,
    custom_resources as cr,
)
from constructs import Construct
import json


class FrontendStack(Stack):
    """
    S3バケット + CloudFront でフロントエンドをホスティングするスタック
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "dev", api_url: str = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.api_url = api_url

        # S3バケット作成（React アプリケーション用）
        self.frontend_bucket = s3.Bucket(
            self,
            f"FrontendBucket-{env_name}",
            bucket_name=f"silverlose-frontend-{env_name}-{Stack.of(self).account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,  # バージョニング有効（ロールバック対応）
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # パブリックアクセスブロック
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=True if env_name != "prod" else False,  # dev環境のみ自動削除
        )

        # CloudFront Origin Access Control (OAC)
        oac = cloudfront.S3OriginAccessControl(
            self,
            f"FrontendOAC-{env_name}",
        )

        # CloudFront Distribution
        self.distribution = cloudfront.Distribution(
            self,
            f"FrontendDistribution-{env_name}",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    self.frontend_bucket,
                    origin_access_control=oac,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True,  # Gzip/Brotli圧縮
            ),
            default_root_object="index.html",
            error_responses=[
                # SPA対応: 404エラーを /index.html にリダイレクト
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_200,  # 日本・アジア・北米・欧州
            comment=f"Silverlose Frontend Distribution - {env_name}",
        )

        # S3バケットポリシー: CloudFrontからのアクセスのみ許可
        self.frontend_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{self.frontend_bucket.bucket_arn}/*"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{Stack.of(self).account}:distribution/{self.distribution.distribution_id}"
                    }
                },
            )
        )

        # config.json を S3 にアップロード
        if self.api_url:
            config_content = json.dumps({"apiUrl": self.api_url})

            # AwsCustomResourceを使用してconfig.jsonをS3にアップロード
            upload_config = cr.AwsCustomResource(
                self,
                f"UploadConfig-{env_name}",
                on_create=cr.AwsSdkCall(
                    service="S3",
                    action="putObject",
                    parameters={
                        "Bucket": self.frontend_bucket.bucket_name,
                        "Key": "config.json",
                        "Body": config_content,
                        "ContentType": "application/json",
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(f"config-{env_name}"),
                ),
                on_update=cr.AwsSdkCall(
                    service="S3",
                    action="putObject",
                    parameters={
                        "Bucket": self.frontend_bucket.bucket_name,
                        "Key": "config.json",
                        "Body": config_content,
                        "ContentType": "application/json",
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(f"config-{env_name}"),
                ),
                policy=cr.AwsCustomResourcePolicy.from_statements([
                    iam.PolicyStatement(
                        actions=["s3:PutObject"],
                        resources=[f"{self.frontend_bucket.bucket_arn}/config.json"],
                    )
                ]),
            )

        # タグ追加
        Tags.of(self).add("Env", env_name)
        Tags.of(self).add("Project", "silverlose")
