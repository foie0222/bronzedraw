from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import sys

# 環境変数からDATABASE_URLを取得
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("Error: The DATABASE_URL environment variable is not set. Please set it to a valid database connection string.")

# echo=True は開発環境のみで有効化
ECHO_SQL = os.getenv("ENV", "development") == "development"

# エンジン作成
engine = create_engine(
    DATABASE_URL,
    echo=ECHO_SQL,
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
