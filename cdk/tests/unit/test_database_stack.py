import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
from stacks.network_stack import NetworkStack
from stacks.database_stack import DatabaseStack


def test_aurora_cluster_created():
    """Auroraクラスターが作成されることを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    template = Template.from_stack(db_stack)

    # DBクラスターが作成されていることを確認
    template.resource_count_is("AWS::RDS::DBCluster", 1)

    # エンジンがAurora PostgreSQLであることを確認
    template.has_resource_properties("AWS::RDS::DBCluster", {
        "Engine": "aurora-postgresql",
        "DatabaseName": "bronzedraw"
    })


def test_serverless_v2_configuration():
    """Serverless v2の設定が正しいことを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    template = Template.from_stack(db_stack)

    # Serverless v2スケーリング設定を確認
    template.has_resource_properties("AWS::RDS::DBCluster", {
        "ServerlessV2ScalingConfiguration": {
            "MinCapacity": 0.5,
            "MaxCapacity": 1.0
        }
    })


def test_data_api_enabled():
    """Data APIが有効化されていることを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    template = Template.from_stack(db_stack)

    # Data APIが有効化されていることを確認
    template.has_resource_properties("AWS::RDS::DBCluster", {
        "EnableHttpEndpoint": True
    })


def test_secrets_manager_integration():
    """Secrets Managerが統合されていることを確認"""
    app = cdk.App()
    network_stack = NetworkStack(app, "TestNetworkStack", env_name="test")
    db_stack = DatabaseStack(
        app,
        "TestDatabaseStack",
        env_name="test",
        vpc=network_stack.vpc,
        aurora_sg=network_stack.aurora_sg
    )
    template = Template.from_stack(db_stack)

    # Secrets Managerシークレットが作成されていることを確認
    template.resource_count_is("AWS::SecretsManager::Secret", 1)


def test_backup_configuration():
    """バックアップ設定が正しいことを確認"""
    # dev環境
    app_dev = cdk.App()
    network_stack_dev = NetworkStack(app_dev, "TestNetworkStackDev", env_name="test")
    db_stack_dev = DatabaseStack(
        app_dev,
        "TestDatabaseStackDev",
        env_name="dev",
        vpc=network_stack_dev.vpc,
        aurora_sg=network_stack_dev.aurora_sg
    )
    template_dev = Template.from_stack(db_stack_dev)
    template_dev.has_resource_properties("AWS::RDS::DBCluster", {
        "BackupRetentionPeriod": 1
    })

    # prod環境
    app_prod = cdk.App()
    network_stack_prod = NetworkStack(app_prod, "TestNetworkStackProd", env_name="test")
    db_stack_prod = DatabaseStack(
        app_prod,
        "TestDatabaseStackProd",
        env_name="prod",
        vpc=network_stack_prod.vpc,
        aurora_sg=network_stack_prod.aurora_sg
    )
    template_prod = Template.from_stack(db_stack_prod)
    template_prod.has_resource_properties("AWS::RDS::DBCluster", {
        "BackupRetentionPeriod": 7
    })


def test_deletion_protection():
    """削除保護が環境に応じて設定されることを確認"""
    # dev環境
    app_dev = cdk.App()
    network_stack_dev = NetworkStack(app_dev, "TestNetworkStackDev2", env_name="test")
    db_stack_dev = DatabaseStack(
        app_dev,
        "TestDatabaseStackDev2",
        env_name="dev",
        vpc=network_stack_dev.vpc,
        aurora_sg=network_stack_dev.aurora_sg
    )
    template_dev = Template.from_stack(db_stack_dev)
    template_dev.has_resource_properties("AWS::RDS::DBCluster", {
        "DeletionProtection": False
    })

    # prod環境
    app_prod = cdk.App()
    network_stack_prod = NetworkStack(app_prod, "TestNetworkStackProd2", env_name="test")
    db_stack_prod = DatabaseStack(
        app_prod,
        "TestDatabaseStackProd2",
        env_name="prod",
        vpc=network_stack_prod.vpc,
        aurora_sg=network_stack_prod.aurora_sg
    )
    template_prod = Template.from_stack(db_stack_prod)
    template_prod.has_resource_properties("AWS::RDS::DBCluster", {
        "DeletionProtection": True
    })


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
    template = Template.from_stack(db_stack)

    # 必要なアウトプットがエクスポートされることを確認
    template.has_output("DBClusterEndpoint", {})
    template.has_output("DBClusterIdentifier", {})
    template.has_output("DBSecretArn", {})
    template.has_output("DBName", {})
