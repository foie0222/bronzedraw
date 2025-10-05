# Backend (FastAPI)

JAN-URL変換APIのバックエンド

## 技術スタック

- FastAPI (Python 3.12)
- SQLAlchemy (ORM)
- PostgreSQL / Aurora PostgreSQL
- Mangum (Lambda adapter)

## ローカル開発

### Docker Composeで起動（推奨）
```bash
# プロジェクトルートから
docker compose up backend
```

### 直接起動
```bash
# 仮想環境作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
export DATABASE_URL="postgresql://bronzedraw:bronzedraw_dev_password@localhost:5432/bronzedraw"
export DEBUG="true"

# 起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API エンドポイント

### 開発環境
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### エンドポイント一覧

#### `GET /api/convert`
JANコードからURLを取得

**クエリパラメータ:**
- `jan`: JANコード (13桁)

**レスポンス例:**
```json
{
  "jan_code": "4571657070839",
  "url": "https://www.goldwin.co.jp/ap/item/i/m/NP12503",
  "brand": "The North Face",
  "product_name": "Mountain Down Jacket"
}
```

#### `POST /api/jan`
JANコードとURLのマッピングを登録

**リクエストボディ:**
```json
{
  "jan_code": "4571657070839",
  "url": "https://example.com/product",
  "brand": "Sample Brand",
  "product_name": "Sample Product"
}
```

## テスト

```bash
# テスト実行（準備中）
pytest
```

## 環境変数

### ローカル開発
- `DATABASE_URL`: PostgreSQL接続文字列
- `DEBUG`: デバッグモード (`true`/`false`)

### Lambda環境
- `DB_SECRET_ARN`: Secrets Manager ARN
- `DB_CLUSTER_ENDPOINT`: Aurora エンドポイント
- `DB_NAME`: データベース名 (デフォルト: `bronzedraw`)
- `ENV`: 環境名 (`dev`/`prod`)

## プロジェクト構成

```
backend/
├── app/
│   ├── main.py          # FastAPIアプリケーション
│   └── database.py      # DB接続・モデル定義
├── db/
│   └── init.sql         # 初期データ
├── requirements.txt     # 本番依存関係
├── Dockerfile          # Docker設定
└── README.md
```

## データベースマイグレーション

現在はinit.sqlで初期化。将来的にAlembicなどの導入を検討。

## デバッグ

```bash
# ログ確認
docker compose logs -f backend

# コンテナ内に入る
docker compose exec backend bash

# データベース接続確認
docker compose exec backend python -c "from app.database import engine; print(engine.url)"
```
