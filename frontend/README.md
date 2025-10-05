# Frontend (React + TypeScript + Vite)

JAN-URL変換アプリのフロントエンド

## 技術スタック

- React 19
- TypeScript 5.9
- Vite 7
- ESLint 9

## ローカル開発

### Docker Composeで起動（推奨）
```bash
# プロジェクトルートから
docker compose up frontend
```

### 直接起動
```bash
# 依存関係インストール
yarn install

# 開発サーバー起動
yarn dev
```

開発サーバー: http://localhost:5173

## ビルド

```bash
# 本番ビルド
yarn build

# ビルド結果のプレビュー
yarn preview
```

ビルド成果物は `dist/` ディレクトリに出力されます。

## リント

```bash
# ESLintチェック
yarn lint
```

## 環境変数

### ローカル開発
- `VITE_API_URL`: バックエンドAPIのURL（デフォルト: `http://localhost:8000`）

### 本番環境
- CloudFrontデプロイ後、S3の `config.json` からAPI URLを動的に読み込み

## プロジェクト構成

```
frontend/
├── src/
│   ├── App.tsx          # メインコンポーネント
│   └── main.tsx         # エントリーポイント
├── public/              # 静的ファイル
├── dist/                # ビルド出力（生成される）
├── package.json
├── vite.config.ts       # Vite設定
├── tsconfig.json        # TypeScript設定
└── README.md
```

## デプロイ

```bash
# ビルド
yarn build

# S3へアップロード
aws s3 sync dist/ s3://bronzedraw-frontend-{env}-{account}/

# CloudFrontキャッシュ無効化
aws cloudfront create-invalidation --distribution-id {id} --paths "/*"
```

詳細はルートREADMEを参照してください。

## トラブルシューティング

### ポート5173が使用中
```bash
# プロセスを確認
lsof -ti:5173

# プロセスを終了
kill -9 $(lsof -ti:5173)
```

### API接続エラー
- `VITE_API_URL`が正しく設定されているか確認
- バックエンドが起動しているか確認（http://localhost:8000/docs）
