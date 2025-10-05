import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from stacks.network_stack import NetworkStack
from stacks.database_stack import DatabaseStack
from stacks.api_stack import ApiStack


def test_lambda_function_created():
    """Lambda関数が作成されることを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    api_stack = ApiStack(
        app,
        "TestApiStack",
        env_name="test",
        vpc=network_stack.vpc,
        lambda_sg=network_stack.lambda_sg,
        db_cluster=db_stack.db_cluster,
        db_secret=db_stack.db_secret
    )
    template = Template.from_stack(api_stack)

    # Lambda関数が作成されていることを確認
    template.resource_count_is("AWS::Lambda::Function", 1)

    # Python 3.11ランタイムであることを確認
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.11"
    })


def test_lambda_configuration():
    """Lambdaの設定が正しいことを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    api_stack = ApiStack(
        app,
        "TestApiStack",
        env_name="test",
        vpc=network_stack.vpc,
        lambda_sg=network_stack.lambda_sg,
        db_cluster=db_stack.db_cluster,
        db_secret=db_stack.db_secret
    )
    template = Template.from_stack(api_stack)

    # タイムアウトとメモリサイズを確認
    template.has_resource_properties("AWS::Lambda::Function", {
        "Timeout": 30,
        "MemorySize": 512
    })


def test_lambda_environment_variables():
    """Lambda環境変数が正しく設定されることを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    api_stack = ApiStack(
        app,
        "TestApiStack",
        env_name="test",
        vpc=network_stack.vpc,
        lambda_sg=network_stack.lambda_sg,
        db_cluster=db_stack.db_cluster,
        db_secret=db_stack.db_secret
    )
    template = Template.from_stack(api_stack)

    # 環境変数が設定されていることを確認
    template.has_resource_properties("AWS::Lambda::Function", {
        "Environment": {
            "Variables": {
                "ENV": "test",
                "DB_NAME": "bronzedraw"
            }
        }
    })


def test_api_gateway_created():
    """API Gatewayが作成されることを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    api_stack = ApiStack(
        app,
        "TestApiStack",
        env_name="test",
        vpc=network_stack.vpc,
        lambda_sg=network_stack.lambda_sg,
        db_cluster=db_stack.db_cluster,
        db_secret=db_stack.db_secret
    )
    template = Template.from_stack(api_stack)

    # REST APIが作成されていることを確認
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_lambda_iam_permissions():
    """LambdaのIAM権限が正しく設定されることを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    api_stack = ApiStack(
        app,
        "TestApiStack",
        env_name="test",
        vpc=network_stack.vpc,
        lambda_sg=network_stack.lambda_sg,
        db_cluster=db_stack.db_cluster,
        db_secret=db_stack.db_secret
    )
    template = Template.from_stack(api_stack)

    # IAMロールが作成されていることを確認（Lambda実行ロール + API Gateway CloudWatchロール）
    # 少なくとも2つのロールが存在することを確認
    resources = template.find_resources("AWS::IAM::Role")
    assert len(resources) >= 2


def test_outputs_exported():
    """アウトプットが正しくエクスポートされることを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    api_stack = ApiStack(
        app,
        "TestApiStack",
        env_name="test",
        vpc=network_stack.vpc,
        lambda_sg=network_stack.lambda_sg,
        db_cluster=db_stack.db_cluster,
        db_secret=db_stack.db_secret
    )
    template = Template.from_stack(api_stack)

    # 必要なアウトプットがエクスポートされることを確認
    template.has_output("ApiUrl", {})
    template.has_output("LambdaFunctionArn", {})
    template.has_output("LambdaFunctionName", {})
