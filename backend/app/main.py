from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db, JanUrlMappingModel

app = FastAPI(title="JAN-URL Conversion API", version="1.0.0")

# CORS設定（CloudFrontからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンに制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JanUrlMapping(BaseModel):
    jan_code: str
    url: str
    brand: Optional[str] = None
    product_name: Optional[str] = None

    class Config:
        from_attributes = True


@app.get("/")
def read_root():
    """ヘルスチェック用エンドポイント"""
    return {"message": "JAN-URL Conversion API", "status": "healthy"}


@app.get("/api/convert", response_model=JanUrlMapping)
async def convert_jan_to_url(jan: str, db: AsyncSession = Depends(get_db)):
    """
    JANコードからURLに変換するAPI

    Args:
        jan: JANコード（13桁）
        db: データベースセッション

    Returns:
        JanUrlMapping: JAN-URLマッピング情報
    """
    result = await db.execute(
        select(JanUrlMappingModel).where(JanUrlMappingModel.jan_code == jan)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail=f"JAN code '{jan}' not found"
        )

    return mapping


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """ヘルスチェック用エンドポイント（DB接続確認含む）"""
    try:
        # DB接続確認
        await db.execute(select(1))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


# Lambda用のハンドラー（Mangum使用）
from mangum import Mangum
handler = Mangum(app)
