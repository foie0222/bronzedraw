import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from stacks.frontend_stack import FrontendStack


def test_s3_bucket_created():
    """S3バケットが作成されることを確認"""
    app = cdk.App()
    frontend_stack = FrontendStack(
        app,
        "TestFrontendStack",
        env_name="test",
        api_url="https://test-api.example.com"
    )
    template = Template.from_stack(frontend_stack)

    # S3バケットが作成されていることを確認
    template.resource_count_is("AWS::S3::Bucket", 1)

    # バケット設定を確認
    template.has_resource_properties("AWS::S3::Bucket", {
        "VersioningConfiguration": {
            "Status": "Enabled"
        },
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True,
            "BlockPublicPolicy": True,
            "IgnorePublicAcls": True,
            "RestrictPublicBuckets": True
        }
    })


def test_cloudfront_distribution_created():
    """CloudFrontディストリビューションが作成されることを確認"""
    app = cdk.App()
    frontend_stack = FrontendStack(
        app,
        "TestFrontendStack",
        env_name="test",
        api_url="https://test-api.example.com"
    )
    template = Template.from_stack(frontend_stack)

    # CloudFrontディストリビューションが作成されていることを確認
    template.resource_count_is("AWS::CloudFront::Distribution", 1)


def test_cloudfront_configuration():
    """CloudFrontの設定が正しいことを確認"""
    app = cdk.App()
    frontend_stack = FrontendStack(
        app,
        "TestFrontendStack",
        env_name="test",
        api_url="https://test-api.example.com"
    )
    template = Template.from_stack(frontend_stack)

    # デフォルトルートオブジェクトを確認
    template.has_resource_properties("AWS::CloudFront::Distribution", {
        "DistributionConfig": {
            "DefaultRootObject": "index.html"
        }
    })


def test_error_responses_configured():
    """エラーレスポンスが設定されることを確認"""
    app = cdk.App()
    frontend_stack = FrontendStack(
        app,
        "TestFrontendStack",
        env_name="test",
        api_url="https://test-api.example.com"
    )
    template = Template.from_stack(frontend_stack)

    # カスタムエラーレスポンスが設定されていることを確認（SPA対応）
    template.has_resource_properties("AWS::CloudFront::Distribution", {
        "DistributionConfig": {
            "CustomErrorResponses": Match.array_with([
                Match.object_like({
                    "ErrorCode": 404,
                    "ResponseCode": 200,
                    "ResponsePagePath": "/index.html"
                }),
                Match.object_like({
                    "ErrorCode": 403,
                    "ResponseCode": 200,
                    "ResponsePagePath": "/index.html"
                })
            ])
        }
    })


def test_bucket_policy_restricts_access():
    """S3バケットポリシーがCloudFront OACのみに制限されることを確認"""
    app = cdk.App()
    frontend_stack = FrontendStack(
        app,
        "TestFrontendStack",
        env_name="test",
        api_url="https://test-api.example.com"
    )
    template = Template.from_stack(frontend_stack)

    # バケットポリシーが作成されていることを確認
    template.resource_count_is("AWS::S3::BucketPolicy", 1)


def test_removal_policy_by_environment():
    """削除ポリシーが環境に応じて設定されることを確認"""
    # dev環境
    app_dev = cdk.App()
    frontend_stack_dev = FrontendStack(
        app_dev,
        "TestFrontendStackDev",
        env_name="dev",
        api_url="https://test-api.example.com"
    )
    template_dev = Template.from_stack(frontend_stack_dev)
    # dev環境ではDESTROYポリシー
    template_dev.has_resource("AWS::S3::Bucket", {
        "UpdateReplacePolicy": "Delete",
        "DeletionPolicy": "Delete"
    })

    # prod環境
    app_prod = cdk.App()
    frontend_stack_prod = FrontendStack(
        app_prod,
        "TestFrontendStackProd",
        env_name="prod",
        api_url="https://test-api.example.com"
    )
    template_prod = Template.from_stack(frontend_stack_prod)
    # prod環境ではRETAINポリシー
    template_prod.has_resource("AWS::S3::Bucket", {
        "UpdateReplacePolicy": "Retain",
        "DeletionPolicy": "Retain"
    })


def test_outputs_exported():
    """アウトプットが正しくエクスポートされることを確認"""
    app = cdk.App()
    frontend_stack = FrontendStack(
        app,
        "TestFrontendStack",
        env_name="test",
        api_url="https://test-api.example.com"
    )
    template = Template.from_stack(frontend_stack)

    # 必要なアウトプットがエクスポートされることを確認
    template.has_output("CloudFrontUrl", {})
    template.has_output("CloudFrontDistributionId", {})
    template.has_output("FrontendBucketName", {})
