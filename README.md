# Bronzedraw

JAN-URL変換APIを提供するWebアプリケーション

## アーキテクチャ

```
[ユーザー]
    |
    v
[CloudFront] --> [S3 (React Frontend)]
    |
    v
[API Gateway] --> [Lambda (FastAPI)] --> [Aurora PostgreSQL Serverless v2]
```

詳細なアーキテクチャ図: [システム構成図](https://drive.google.com/file/d/1eCm5B628DcuFPQbLN1XyuJ_sSiIeOOS0/view?usp=sharing)

## 技術スタック

### フロントエンド
- React + TypeScript + Vite
- CloudFront + S3

### バックエンド
- FastAPI (Python 3.12)
- AWS Lambda + API Gateway
- Aurora PostgreSQL Serverless v2

### インフラ
- AWS CDK (Python)
- Docker (ローカル開発)

## 開発環境セットアップ

### 必要なツール
- Python 3.12+
- Node.js 18+ (推奨: 22 LTS)
- Docker & Docker Compose
- AWS CLI
- AWS CDK CLI

### ローカル開発

```bash
# すべてのサービスを起動（DB + バックエンド + フロントエンド）
docker compose up
```

起動後のURL:
- フロントエンド: http://localhost:5173
- バックエンドAPI: http://localhost:8000
- API Docs: http://localhost:8000/docs

個別の開発環境については各ディレクトリのREADMEを参照してください。

## デプロイ

### CDKデプロイ
```bash
cd cdk
pip install -r requirements.txt
cdk bootstrap  # 初回のみ
cdk deploy --all
```

### フロントエンドデプロイ
```bash
cd frontend
yarn build
aws s3 sync dist/ s3://bronzedraw-frontend-{env}-{account}/
aws cloudfront create-invalidation --distribution-id {id} --paths "/*"
```

## テスト

### バックエンド
```bash
cd backend
pytest
```

### CDK
```bash
cd cdk
pytest tests/
```

## 環境変数

### ローカル開発
- `DATABASE_URL`: PostgreSQL接続文字列
- `DEBUG`: デバッグモード (true/false)

### Lambda
- `DB_SECRET_ARN`: Secrets Manager ARN
- `DB_CLUSTER_ENDPOINT`: Aurora エンドポイント
- `DB_NAME`: データベース名

## プロジェクト構成

```
bronzedraw/
├── backend/          # FastAPI アプリケーション
├── frontend/         # React アプリケーション
├── cdk/             # AWS CDK インフラコード
│   ├── stacks/      # CDKスタック定義
│   └── tests/       # CDKユニットテスト
└── README.md
```

## データベーススキーマ

### jan_url_mapping
| カラム | 型 | 説明 |
|--------|-----|------|
| id | SERIAL | 主キー |
| jan_code | VARCHAR(13) | JANコード（ユニーク） |
| url | TEXT | 商品URL |
| brand | VARCHAR(100) | ブランド名 |
| product_name | VARCHAR(255) | 商品名 |
| created_at | TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | 更新日時 |

## Aurora Query Editorでのデータ管理

1. AWSコンソール → RDS → Query Editor
2. Auroraクラスター選択
3. データベース名: `bronzedraw`
4. Secrets Manager認証情報で接続
5. SQLを実行

## 主要コマンド

```bash
# CDKスタック一覧
cd cdk && cdk list

# CDK差分確認
cdk diff BronzedrawApiStack-dev

# Dockerログ確認
docker compose logs -f backend

# テスト実行
pytest -v

# 一時ファイルクリーンアップ
rm -rf cdk/cdk.out/ /tmp/jsii-kernel-* /tmp/tmp*
```

## トラブルシューティング

### Lambdaデプロイエラー
- Docker Desktopが起動しているか確認
- CDKがPython 3.12のbundling imageをpullできているか確認

### データベース接続エラー
- ローカル: `DATABASE_URL`環境変数を確認
- Lambda: Secrets ManagerとVPCセキュリティグループを確認

### テストでディスク容量不足
```bash
rm -rf cdk/cdk.out/
```

## 参考リンク

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Aurora Serverless v2](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html)
