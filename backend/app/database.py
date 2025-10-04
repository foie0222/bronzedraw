from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, func
import os

# 環境変数からDATABASE_URLを取得
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://silverlose:silverlose_dev_password@localhost:5432/silverlose")

# PostgreSQL用の接続URL（asyncpg使用）
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# エンジン作成
engine = create_async_engine(DATABASE_URL, echo=True)

# セッションファクトリ
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
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
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
