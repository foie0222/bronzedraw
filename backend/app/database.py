from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import sys
import json

# 環境変数からDATABASE_URLを取得（ローカルDocker用）
DATABASE_URL = os.getenv("DATABASE_URL")

# DATABASE_URLが設定されていない場合、Secrets Managerから取得（Lambda用）
if not DATABASE_URL:
    db_secret_arn = os.getenv("DB_SECRET_ARN")
    db_endpoint = os.getenv("DB_CLUSTER_ENDPOINT")
    db_name = os.getenv("DB_NAME", "bronzedraw")

    if db_secret_arn and db_endpoint:
        # Secrets Managerから認証情報を取得
        import boto3
        secrets_client = boto3.client('secretsmanager')
        secret_value = secrets_client.get_secret_value(SecretId=db_secret_arn)
        secret = json.loads(secret_value['SecretString'])

        # DATABASE_URLを構築
        DATABASE_URL = f"postgresql://{secret['username']}:{secret['password']}@{db_endpoint}:5432/{db_name}"
    else:
        sys.exit("Error: Neither DATABASE_URL nor DB_SECRET_ARN/DB_CLUSTER_ENDPOINT is set.")

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# エンジン作成
engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600
)

# セッションファクトリ
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# Base作成
Base = declarative_base()


# モデル定義
class JanUrlMappingModel(Base):
    __tablename__ = "jan_url_mapping"

    id = Column(Integer, primary_key=True, index=True)
    jan_code = Column(String(13), unique=True, nullable=False, index=True)
    url = Column(Text, nullable=False)
    brand = Column(String(100))
    product_name = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 依存関係注入用
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
