FROM node:20-alpine

WORKDIR /app

# package.jsonとyarn.lockをコピー
COPY package.json yarn.lock ./

# 依存関係をインストール
RUN yarn install --frozen-lockfile

# アプリケーションコードをコピー
COPY . .

# ポート5173を公開（Viteのデフォルトポート）
EXPOSE 5173

# Vite開発サーバーを起動
CMD ["yarn", "dev", "--host", "0.0.0.0"]
