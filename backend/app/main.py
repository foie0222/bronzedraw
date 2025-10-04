from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

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


# サンプルデータ（後でAurora PostgreSQLに置き換え）
SAMPLE_DATA = {
    "4571657070839": {
        "jan_code": "4571657070839",
        "url": "https://www.goldwin.co.jp/ap/item/i/m/NP12503",
        "brand": "The North Face",
        "product_name": "Mountain Down Jacket",
    },
    "4548913619937": {
        "jan_code": "4548913619937",
        "url": "https://www.goldwin.co.jp/ap/item/i/m/NP62236",
        "brand": "The North Face",
        "product_name": "Nuptse Jacket",
    },
}


@app.get("/")
def read_root():
    """ヘルスチェック用エンドポイント"""
    return {"message": "JAN-URL Conversion API", "status": "healthy"}


@app.get("/api/convert", response_model=JanUrlMapping)
def convert_jan_to_url(jan: str):
    """
    JANコードからURLに変換するAPI

    Args:
        jan: JANコード（13桁）

    Returns:
        JanUrlMapping: JAN-URLマッピング情報
    """
    if jan not in SAMPLE_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"JAN code '{jan}' not found"
        )

    return SAMPLE_DATA[jan]


@app.get("/health")
def health_check():
    """ヘルスチェック用エンドポイント"""
    return {"status": "ok"}


# Lambda用のハンドラー（Mangum使用）
from mangum import Mangum
handler = Mangum(app)
