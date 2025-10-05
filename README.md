## システム構成

### 対象環境
- dev 環境
- 後から他の環境も追加できるように構築する
- 全ての AWS リソースには Env: dev のタグが付くようにする。

### リージョン
- **ap-northeast-1**（東京リージョン）

### トラフィック推定
- **1日平均利用者数**: 約256人
- **API呼び出し数**（JAN-URL変換API）:
  - 月間: 約23,000回
  - 1日平均: 約768回
  - ピーク時（土日想定）: 約1,536回/日

## アーキテクチャ概要

### 全体構成図
```
[エンドユーザー（スマートフォン）]
        |
        | HTTPS
        v
    [AWS WAF] ← セキュリティフィルタリング
        |
        v
[CloudFront（CDN）]
        |
        +---> [S3バケット]
        |     |- フロントエンド（React + TypeScript + Vite）
        |
        +---> [API Gateway]
                    |
                    v
              [Lambda Function]
              （JAN-URL変換API）
              - VPC内プライベートサブネット配置
                    |
                    v
              [Aurora PostgreSQL Serverless v2]
              （JAN-URLマッピングテーブル）
              - VPC内プライベートサブネット配置
              - RDS Data API有効
              - Query Editor対応

[データベース管理]
- RDS Query Editor: AWSコンソールから直接SQL実行
- RDS Data API: EC2不要のマネージドアクセス

[監視・セキュリティ]
- CloudWatch: ログ・メトリクス・アラーム
- GuardDuty: 脅威検知
- CloudTrail: API操作ログ（監査）
- SNS: アラート通知
```

### 主要コンポーネント

#### フロントエンド
- **技術スタック**: React（React + TypeScript + Vite）
- **ホスティング**: S3 + CloudFront
- **配信方式**: 静的コンテンツとしてCDN経由で配信

#### バックエンドAPI
- **技術スタック**: FastAPI（Python）
- **実行環境**: AWS Lambda ※要確認
- **API管理**: API Gateway（REST API）
- **機能**: JAN-URL変換APIのみ

#### データベース
- **RDBMS**: Amazon Aurora PostgreSQL Serverless v2 ※PostgreSQLでよいか要確認
- **用途**: JAN-URLマッピングテーブルの管理
- **更新頻度**:月次で商品入れ替え
- **管理方法**: RDS Query Editor（AWSコンソール）、RDS Data API

---

## 各AWSサービスの要件

### 1. Amazon S3

#### バケット構成
- **環境ごとにバケット**: 1個

#### 用途
- Reactアプリケーションのビルド成果物（HTML/CSS/JavaScript）の配置
- 静的ウェブサイトホスティング

#### 設定要件
- バケットポリシーでCloudFrontからのアクセスのみ許可（アプリ用）
- バージョニング: 有効化（ロールバック対応）
- 暗号化: SSE-S3（デフォルト暗号化）
- パブリックアクセス: ブロック（CloudFront経由のみ）
- ライフサイクルポリシー: 必要に応じて設定

---

### 2. Amazon CloudFront

#### ディストリビューション構成
- 環境ごとに1個

#### 設定要件
- オリジン: S3バケット（OAC経由）
- SSL/TLS証明書: AWS Certificate Manager（ACM）で発行
- キャッシュ動作:
  - デフォルト: キャッシュあり
- カスタムエラーレスポンス: SPAのルーティング対応（404 → /index.html）
- 圧縮: 有効化（Gzip/Brotli）
- WAF統合: AWS WAFと連携

---

### 3. AWS WAF（Web Application Firewall）

#### WAF構成
- 環境ごとに1個（CloudFrontに関連付け）

#### ルール設定
- AWS Managed Rules を利用、詳細は別途検討

#### ログ
- 詳細は別途検討

---

### 4. AWS Lambda ※詳細の仕様は要確認

#### 関数構成
- 環境ごとに1関数

#### 関数仕様
- **ランタイム**: Python 3.11以上
- **フレームワーク**: FastAPI + Mangum（Lambda adapter）
- **メモリ**: 512MB（初期設定、必要に応じて調整）
- **タイムアウト**: 30秒
- **同時実行数**: 予約なし（オンデマンド）

#### 環境変数
- `DATABASE_CLUSTER_ARN`: Auroraクラスターのリソース名
- `DATABASE_SECRET_ARN`: Secrets ManagerのARN
- `DATABASE_NAME`: データベース名
- `ENV`: 環境識別子（stg/prod）

#### VPC設定
- VPC内に配置（Aurora接続のため）
- プライベートサブネット × 2（マルチAZ）

#### デプロイ方式
- コード管理: GitHub
- パッケージング: Lambdaレイヤー利用（依存ライブラリ）
- CI/CD: GitHub Actions

---

### 5. Amazon API Gateway ※詳細の仕様は要確認

#### API構成
- 環境ごとに1個

#### API仕様
- **タイプ**: REST API
- **認証**: なし（パブリックアクセス）
  - 必要に応じてAPI Key認証を検討
- **エンドポイント**: リージョナル
- **CORS**: 有効化（CloudFrontのオリジンを許可）

#### リソース設計 ※仮で記載しているだけなので要検討
- `GET /api/convert?jan={JAN_CODE}`: JAN-URL変換API

#### レスポンス例 ※仮で記載しているだけなので要検討
```json
{
  "jan_code": "4571657070839",
  "url": "https://www.goldwin.co.jp/ap/item/i/m/NP12503",
  "brand": "The North Face"
}
```

#### スロットリング
- レート制限: 1000リクエスト/秒（初期設定）
- バーストリミット: 2000（初期設定）

#### ログ設定
- アクセスログ: CloudWatch Logsへ出力
- 実行ログ: INFO レベル（エラー詳細含む）

---

### 6. Amazon Aurora PostgreSQL Serverless v2 ※詳細の仕様は要確認

#### クラスター構成
- **テスト環境**: マルチAZ構成
- **本番環境**: マルチAZ構成
- **ライター**: 1インスタンス（自動フェイルオーバー対応）
- **リーダー**: 0インスタンス（必要に応じて追加可能）

#### データベース仕様
- **エンジン**: Aurora PostgreSQL 16.x（Serverless v2互換）
- **ACU（Aurora Capacity Units）設定**:
  - 最小ACU: 0.5（約$0.12/ACU/時）
  - 最大ACU: 2.0（初期設定、必要に応じて調整）
  - 自動スケーリング: 有効
- **ストレージ**: Aurora共有ストレージ（自動拡張、最大128TB）
- **ストレージ料金**: $0.10/GB/月
- **I/O料金**: 100万リクエストあたり$0.20

#### データAPI有効化
- **RDS Data API**: 有効
- **Query Editor**: AWSコンソールから利用可能
- **IAM認証**: 有効（Secrets Manager経由）
- **管理方法**: EC2不要、完全マネージド

#### バックアップ
- **自動バックアップ**: 有効（保持期間7日間）
- **バックアップ先**: S3（自動）
- **ポイントインタイムリカバリ**: 有効（5分間隔）
- **スナップショット**: 手動取得可能

#### ネットワーク設定
- VPC内のプライベートサブネット × 2（マルチAZ）
- パブリックアクセス: 無効
- セキュリティグループ: Lambda SGからのインバウンドのみ許可

#### 認証情報管理
- AWS Secrets Managerで管理
- 自動ローテーション: 有効（30日）
- RDS Data API用にARNを使用

#### テーブル設計 ※仮で記載しているだけなので要検討
```sql
CREATE TABLE jan_url_mapping (
    id SERIAL PRIMARY KEY,
    jan_code VARCHAR(13) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    brand VARCHAR(100),
    product_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jan_code ON jan_url_mapping(jan_code);
```

#### Query Editor使用方法
1. AWSコンソール → RDS → Query Editor
2. Auroraクラスターを選択
3. Secrets Managerの認証情報で接続
4. SQLを直接実行（データ投入、確認、メンテナンス）

---

### 7. Amazon VPC

#### VPC構成
- 環境ごとに1個

#### サブネット構成（各VPC）
- **パブリックサブネット**: 2個（AZ-a、AZ-c）
  - NATゲートウェイ配置用
  - インターネットゲートウェイへのルート
- **プライベートサブネット**: 2個（AZ-a、AZ-c）
  - Lambda、Aurora配置用
  - NATゲートウェイへのルート（外部通信用） ※本当に必要か要検討

#### ネットワーク設計
- **CIDR**: 10.0.0.0/16（テスト）、10.1.0.0/16（本番）
- **パブリックサブネット**: 10.0.1.0/24、10.0.2.0/24（テスト）
- **プライベートサブネット**: 10.0.11.0/24、10.0.12.0/24（テスト）
- **NATゲートウェイ**: 各AZに1個（Lambda → 外部API通信用） ※要確認
- **インターネットゲートウェイ**: VPCレベルで1個

#### セキュリティグループ
- **Lambda用SG**: 
  - アウトバウンド: Auroraへの5432ポート、外部HTTPS（443）
- **Aurora用SG**: 
  - インバウンド: Lambda SGからの5432ポートのみ

---

### 8. AWS Secrets Manager

#### シークレット構成
- 環境ごとに1個（Aurora認証情報）

#### 保存内容
- Auroraクラスターのエンドポイント
- データベース名
- マスターユーザー名
- マスターパスワード
- RDS Data API用ARN情報

#### 自動ローテーション
- 有効化（30日周期）
- Lambda関数による自動ローテーション

#### アクセス制御
- Lambda実行ロールからのみアクセス可能（IAMポリシー）
- RDS Data API経由でのアクセス

---

### 9. Amazon CloudWatch

#### ログ管理（例）
- **Lambda関数ログ**: CloudWatch Logs
  - 保持期間: 1年
  - ログレベル: INFO（本番）、DEBUG（テスト）
- **API Gatewayログ**: CloudWatch Logs
  - アクセスログ、実行ログ
  - 保持期間: 1年
- **WAFログ**: CloudWatch Logs
  - 保持期間: 90日
- **VPCフローログ**（オプション）: 
  - ネットワークトラブルシューティング用
  - 保持期間: 30日

#### メトリクス監視（例）
- **Lambda**: 実行時間、エラー率、同時実行数、スロットル
- **API Gateway**: リクエスト数、レイテンシ、4xx/5xxエラー
- **Aurora**: ACU使用率、接続数、レイテンシ、ストレージ使用量
- **CloudFront**: リクエスト数、エラー率、キャッシュヒット率
- **WAF**: ブロックされたリクエスト数、許可されたリクエスト数

#### アラーム設定（例）
- **Lambda関数エラー率**: 5%を超えた場合
- **API Gateway 5xxエラー**: 10回/5分を超えた場合
- **Aurora ACU使用率**: 最大ACUの80%を超えた場合
- **Aurora接続数**: 上限の80%を超えた場合
- **Aurora レプリケーション遅延**: 1秒を超えた場合（マルチAZ）
- **WAF ブロック数**: 異常に多い場合（1000回/5分）

#### 通知方法（例）
- Amazon SNS経由でメール通知
- 通知先メールアドレスは構築時に設定

---

### 11. Amazon SNS（Simple Notification Service）

#### トピック構成 ※詳細の仕様は要確認
- **テスト環境用**: 1トピック（アラート通知）
- **本番環境用**: 1トピック（アラート通知）

#### サブスクリプション
- メール通知: 運用担当者のメールアドレス
- 必要に応じてSlack連携も検討可能

---

### 12. AWS CloudTrail

#### 証跡設定
- **マルチリージョン証跡**: 有効（全リージョンのAPI操作を記録）
- **ログ記録対象**:
  - 管理イベント: すべてのAWS API操作
  - データイベント: S3バケットへのオブジェクト操作（オプション）
- **ログ保存先**: S3バケット（専用）
- **ログファイルの検証**: 有効（改ざん検知）
- **CloudWatch Logsへの配信**: 有効（リアルタイム監視用）

#### 保持期間
- S3: 無期限（ライフサイクルポリシーで90日後にGlacierへ）
- CloudWatch Logs: 90日

---

### 13. Amazon GuardDuty

#### 設定
- **有効化**: テスト環境・本番環境の両方で有効
- **検知対象**:
  - 不審なAPI呼び出し
  - ネットワークトラフィックの異常
  - 侵害されたインスタンスの検知

#### アラート
- 検出結果は CloudWatch Events経由でSNSに通知
- 重要度: HIGH以上のみ通知

#### 保持期間
- 検出結果: 90日（GuardDutyコンソール内）

---

### 14. AWS Certificate Manager（ACM）

#### 証明書
- CloudFront用SSL/TLS証明書
- ドメインはゴールドウィン社と協議して決定
- リージョン: us-east-1（CloudFront用は必須）
- 検証方法: DNS検証（推奨）
- 自動更新: 有効

---

### 15. IAM（Identity and Access Management）

#### ロール構成 ※詳細の仕様は要検討

**Lambda実行ロール**:
- CloudWatch Logsへの書き込み
- Secrets Managerからのシークレット読み取り
- Systems Manager Parameter Storeからのパラメータ読み取り
- VPC ENI作成・管理（VPC内実行のため）
- RDS Data API実行権限（`rds-data:ExecuteStatement`, `rds-data:BatchExecuteStatement`）
- X-Ray（オプション）への書き込み

**CloudFront用ロール**:
- S3バケットへの読み取りアクセス（OAC）

**CloudTrail用ロール**:
- S3バケットへの書き込みアクセス
- CloudWatch Logsへの書き込みアクセス

#### ポリシー原則
- 最小権限の原則に従う
- リソースベースのポリシーを優先
- 明示的な許可のみ、デフォルト拒否

その他必要に応じて

---

## セキュリティ要件

### データ保護
- **個人情報**: 扱わない
- **通信の暗号化**: 
  - HTTPS/TLS通信（CloudFront、API Gateway）
  - Aurora接続時のSSL/TLS
- **データの暗号化**:
  - S3: SSE-S3（サーバー側暗号化）
  - Aurora: ストレージ暗号化有効（AES-256）
  - Secrets Manager: デフォルト暗号化（KMS）

### アクセス制御
- S3バケット: CloudFrontからのアクセスのみ（OAC）
- Aurora: Lambda関数からのみアクセス可能（SG制御 + RDS Data API）
- API Gateway: パブリックアクセス（認証なし） ※要確認
- WAF: 悪意のあるトラフィックをブロック
- RDS Data API: IAM認証、Secrets Manager経由

### ネットワークセキュリティ
- Auroraはプライベートサブネット配置、パブリックアクセス無効
- Lambdaもプライベートサブネット配置
- セキュリティグループで最小限の通信のみ許可
- NACLはデフォルト設定（必要に応じてカスタマイズ）

### 監査・コンプライアンス
- CloudTrail: すべてのAPI操作を記録
- GuardDuty: 脅威検知
- CloudWatch: リアルタイム監視
- 定期的なセキュリティレビュー

---

## 運用要件

### データベース管理

#### データ投入・メンテナンス方法
**RDS Query Editor（推奨）**:
  - AWSコンソールから直接アクセス
  - SQLを実行してデータ投入・確認
  - EC2不要、完全マネージド


#### データ更新フロー ※要検討

### バックアップ
- **Aurora**: 
  - 自動バックアップ（7日間保持）
  - ポイントインタイムリカバリ（5分間隔）
  - 手動スナップショット（重要な変更前に取得）
- **S3**: 
  - バージョニング有効化
  - CloudTrailログは長期保存

### 監視・通知
- CloudWatch Alarmsによる異常検知
- GuardDutyによる脅威検知
- SNS経由でのメール通知
- 通知対象: Sanukite社運用担当者

### ログ保持
- アプリケーションログ: 1年間保持（CloudWatch Logs）
- CloudTrailログ: 無期限（S3、90日後にGlacier）
- WAFログ: 90日間保持
- VPCフローログ: 30日間保持（オプション）

### スケーリング
- Lambda: 自動スケール（デフォルト）
- Aurora Serverless v2: 自動スケール（0.5〜2.0 ACU）
- S3/CloudFront: 自動スケール
- API Gateway: 自動スケール

### デプロイ
- **フロントエンド**: 
  - S3へのファイルアップロード
  - CloudFrontキャッシュ無効化（`/*` パス）
- **バックエンド**: 
  - Lambdaへの関数デプロイ（zip）
  - エイリアス/バージョン管理による段階的デプロイ（予定）
- **データベース**: 
  - Query Editor経由でSQLを実行

### 災害復旧（DR）
- **RTO**: 4時間（目標復旧時間）
- **RPO**: 5分（目標復旧時点、ポイントインタイムリカバリ）
- **復旧手順**:
  1. Auroraスナップショットまたはポイントインタイムリカバリから復元
  2. Lambda関数を再デプロイ
  3. S3からフロントエンドを再デプロイ
  4. 動作確認

---

## コスト見積もり（概算）

### 前提条件
- 月間API呼び出し: 23,000回
- Lambda実行時間: 平均200ms
- Aurora ACU使用率: 平均0.5 ACU（ほぼアイドル）
- CloudFront転送量: 10GB/月（想定）

### 月額コスト概算（本番環境）

| サービス | 項目 | 概算コスト |
|---|---|---|
| Lambda | 実行料金 | 無料枠内 |
| API Gateway | リクエスト料金 | 無料枠内 |
| Aurora Serverless v2 | ACU時間（0.5 ACU × 24h × 30日） | $43 |
| Aurora | ストレージ（10GB） | $1 |
| Aurora | I/O（23,000回/月） | $0.01（無視できる） |
| VPC | NATゲートウェイ × 2 | $65 |
| S3 | ストレージ・転送 | $1-2 |
| CloudFront | 転送量 | $1-2 |
| CloudWatch | ログ・メトリクス | $5-10 |
| Secrets Manager | シークレット管理 | $1 |
| WAF | ルール・リクエスト | $10-15 |
| CloudTrail | 証跡管理 | $5 |
| GuardDuty | 脅威検知 | $5-10 |
| Systems Manager | パラメータストア | 無料枠内 |
| **合計** | | **約$135-155/月** |

### テスト環境
- 本番同等構成のため、同額: **約$135-155/月**

### 両環境合計
- **約$270-310/月**

### コスト最適化案
- PoC期間終了後、不要な環境は削除
- NATゲートウェイは1個のみでも運用可能（冗長性は低下、約$30削減）
- Aurora ACU最大値を1.0に下げる（トラフィック増加時は調整）
- CloudWatch Logsの保持期間を短縮（必要に応じて）
- WAFルールは最小限に抑える（初期はAWS Managed Rulesのみ）

### RDS PostgreSQLとの比較
- RDS PostgreSQL（マルチAZ）: 約$130-160/月（両環境で$260-320/月）
- Aurora Serverless v2: 約$135-155/月（両環境で$270-310/月）
- **ほぼ同額だが、Auroraは管理が楽（EC2不要、Query Editor、自動スケール）**

---

## インフラ管理方針

### Infrastructure as Code（IaC）
- **使用**: AWS CDK（Python）
- **スタック構成**:
  - **NetworkStack**: VPC、サブネット、セキュリティグループ
  - **DatabaseStack**: Aurora PostgreSQL Serverless v2
  - **ApiStack**: Lambda + API Gateway
  - **FrontendStack**: S3 + CloudFront
- **デプロイコマンド**:
  ```bash
  cd cdk
  cdk deploy --all  # 全スタックをデプロイ
  cdk deploy BronzedrawDatabaseStack-dev  # Database Stackのみデプロイ
  ```

### ドキュメント
- 構築手順書（本要件定義書に基づく）
- 設定パラメータ一覧（スプレッドシート等で管理）
- ネットワーク構成図
- 運用手順書（デプロイ、障害対応、バックアップ・リストア）
- データ投入手順書（Query Editor使用方法）

### 引継ぎ
- Sanukite社内で運用継続
- 必要に応じて井上が対応

### 変更管理
- 本番環境への変更は事前に変更申請
- テスト環境で動作確認後に本番反映
- 変更履歴を記録（日時、変更内容、担当者）

---

## リスクと対策

### リスク1: Lambda コールドスタート
- **影響**: 初回リクエストが遅延（数秒）
- **発生確率**: 中
- **対策**: 
  - Provisioned Concurrency（予約済み同時実行数）の検討
  - 定期的なウォームアップLambdaの実行（EventBridge Rule）
  - メモリサイズの最適化

### リスク2: Aurora ACU不足
- **影響**: トラフィック急増時にパフォーマンス低下
- **発生確率**: 低（現在の想定トラフィックでは問題なし）
- **対策**: 
  - 最大ACUを2.0に設定（初期）
  - CloudWatchでACU使用率を監視
  - 必要に応じて最大ACUを引き上げ

### リスク3: スケジュールの遅延
- **影響**: 10/22の判断に間に合わない
- **発生確率**: 中
- **対策**: 
  - テスト環境を優先構築
  - 本番環境は並行して構築
  - クリティカルパスの明確化

### リスク4: コスト超過
- **影響**: 想定外のコスト発生
- **発生確率**: 低
- **対策**: 
  - AWS Cost Explorerで日次監視
  - AWS Budgetsで予算アラート設定（月額$350で通知）
  - 不要なリソースの定期的な見直し

### リスク5: セキュリティインシデント
- **影響**: データ漏洩、サービス停止
- **発生確率**: 低
- **対策**: 
  - WAF、GuardDutyによる脅威検知
  - CloudTrailによる監査ログ
  - 定期的なセキュリティレビュー
  - インシデント対応手順書の作成

---

## 制約事項

1. **開発環境なし**: ローカル環境のみで開発
2. **CI/CD未整備**: 手動デプロイまたは簡易スクリプト
3. **認証機能なし**: APIは誰でもアクセス可能（必要に応じて将来追加）
4. **カスタムドメイン**: ゴールドウィン社と協議中
5. **マルチリージョン構成なし**: 東京リージョンのみ

---

## 次のステップ

### フェーズ1: 要件確定（〜10/4）
1. **10/3（金）14:30**: ゴールドウィン社との打ち合わせ
2. 本要件定義書のレビューと承認
3. 未決定事項の確定（カスタムドメイン、通知先メールアドレス等）

### フェーズ2: 環境準備（10/7〜10/11）
1. AWSアカウント作成（ゴールドウィン社）
2. 初期セットアップ（IAMユーザー、MFA設定等）
3. ネットワーク基盤構築（VPC、サブネット、IGW、NAT Gateway）

### フェーズ3: テスト環境構築（10/14〜10/18）
1. セキュリティ基盤（WAF、GuardDuty、CloudTrail）
2. データベース（Aurora Serverless v2）構築
3. RDS Data API有効化、Query Editor動作確認
4. バックエンドAPI（Lambda、API Gateway）構築
5. フロントエンド（S3、CloudFront）構築
6. 監視設定（CloudWatch、SNS）
7. 動作確認

### フェーズ4: 本番環境構築（10/21〜10/25）
1. テスト環境と同様の手順で本番環境を構築
2. セキュリティ設定の強化
3. 監視・アラート設定の最終確認
4. 本番データ投入（Query Editor経由でJAN-URLマッピング）
5. 総合テスト

### フェーズ5: PoC準備（10/28〜11/1）
1. 本番環境での最終動作確認
2. 運用手順書の整備
3. ゴールドウィン社への操作説明（Query Editor使用方法含む）
4. 11/3リリース判断（10/22予定を再確認）

---

## 変更履歴

| 日付 | 版数 | 変更内容 | 作成者 |
|---|---|---|---|
| 2025/10/02 | 1.0 | 初版作成 | Sanukite |
| 2025/10/02 | 1.1 | 石川氏構成図を反映（WAF、CloudTrail、GuardDuty、Systems Manager追加） | Sanukite |
| 2025/10/02 | 2.0 | RDS PostgreSQL → Aurora PostgreSQL Serverless v2に変更、テスト環境をマルチAZ構成に変更 | Sanukite |

---

## 承認

| 役割 | 氏名 | 承認日 |
|---|---|---|
| プロジェクトマネージャー | | |
| 技術責任者 | | |
| ゴールドウィン社担当者 | | |
| Kotozna CTO（石川氏） | | |

---

## 補足資料

### 参考資料
- Kotozna提供のディスカッション資料（2025/8/18）
- 段階的な取組み計画（PoC → Phase1 → 本番展開A/B）
- Kotozna CTO石川氏提供のAWS構成図

### 用語集
- **PoC**: Proof of Concept（概念実証）
- **JAN**: Japanese Article Number（日本の商品コード）
- **SPA**: Single Page Application
- **OAC**: Origin Access Control（CloudFrontのS3アクセス制御）
- **CDN**: Content Delivery Network
- **WAF**: Web Application Firewall
- **NAT**: Network Address Translation
- **IGW**: Internet Gateway
- **SG**: Security Group
- **NACL**: Network Access Control List
- **RTO**: Recovery Time Objective（目標復旧時間）
- **RPO**: Recovery Point Objective（目標復旧時点）
- **ACU**: Aurora Capacity Unit（Auroraの処理能力単位）
- **RDS Data API**: SQLをHTTP API経由で実行できるサービス

---

## 付録A: Aurora Serverless v2について

### Aurora Serverless v2の特徴
- **自動スケール**: 負荷に応じてACU（処理能力）が自動で増減
- **瞬時のスケーリング**: 秒単位でスケール（v1は分単位）
- **マルチAZ対応**: 高可用性を実現
- **RDS Data API**: EC2不要でデータベース管理が可能
- **Query Editor**: AWSコンソールから直接SQL実行
- **コスト効率**: 低トラフィック時は最小ACUで稼働、コスト抑制

### RDS PostgreSQLとの違い
| 項目 | RDS PostgreSQL | Aurora Serverless v2 |
|---|---|---|
| スケーリング | 手動（インスタンスタイプ変更） | 自動（秒単位） |
| 最小構成コスト | $15-20/月（t3.micro） | $43/月（0.5 ACU） |
| マルチAZ | オプション（2倍コスト） | デフォルト対応 |
| DB管理方法 | EC2踏み台必要 | Query Editor（EC2不要） |
| フェイルオーバー | 1-2分 | 30秒以内 |
| ストレージ | 固定（自動拡張可） | 自動拡張（128TBまで） |

### 今回の採用理由
1. **EC2管理不要**: Query EditorでDB管理が完結
2. **本番同等のテスト環境**: マルチAZがデフォルト
3. **コスト**: RDSとほぼ同額
4. **運用の簡素化**: 自動スケール、自動フェイルオーバー
5. **将来の拡張性**: トラフィック増加に柔軟に対応

---

## 付録B: 構築チェックリスト

### VPCネットワーク
- [ ] VPC作成（CIDR: 10.0.0.0/16 or 10.1.0.0/16）
- [ ] パブリックサブネット × 2作成
- [ ] プライベートサブネット × 2作成
- [ ] インターネットゲートウェイ作成・アタッチ
- [ ] NATゲートウェイ × 2作成（各パブリックサブネット）
- [ ] ルートテーブル設定（パブリック・プライベート）
- [ ] セキュリティグループ作成（Lambda用、Aurora用）

### セキュリティ基盤
- [ ] CloudTrail有効化・S3バケット作成
- [ ] GuardDuty有効化
- [ ] AWS WAF作成・CloudFrontに関連付け
- [ ] AWS Config有効化（オプション）

### データベース
- [ ] Aurora Serverless v2クラスター作成
- [ ] ACU設定（最小0.5、最大2.0）
- [ ] RDS Data API有効化
- [ ] Secrets Managerでパスワード管理
- [ ] セキュリティグループ設定
- [ ] Query Editor接続確認
- [ ] 初期テーブル作成（Query Editor経由）
- [ ] 自動バックアップ設定確認

### バックエンドAPI
- [ ] Lambda関数作成
- [ ] VPC設定（プライベートサブネット配置）
- [ ] IAM実行ロール作成・アタッチ（RDS Data API権限含む）
- [ ] 環境変数設定（クラスターARN、シークレットARN等）
- [ ] API Gateway作成
- [ ] Lambda統合設定
- [ ] CORS設定

### フロントエンド
- [ ] S3バケット作成（アプリ用）
- [ ] S3バケット作成（CloudTrailログ用）
- [ ] バケットポリシー設定
- [ ] CloudFront ディストリビューション作成
- [ ] ACM証明書作成（us-east-1）
- [ ] OAC設定
- [ ] カスタムエラーページ設定

### 監視・通知
- [ ] CloudWatch Logs設定（Lambda、API Gateway）
- [ ] CloudWatch Alarms作成（Aurora ACU含む）
- [ ] SNSトピック作成
- [ ] メール通知サブスクリプション設定
- [ ] Systems Manager Parameter Store設定

### 動作確認
- [ ] フロントエンドアクセス確認
- [ ] API動作確認
- [ ] データベース接続確認（RDS Data API）
- [ ] Query Editor動作確認
- [ ] エラーハンドリング確認
- [ ] ログ出力確認
- [ ] アラート通知テスト
- [ ] Aurora自動スケール確認（負荷テスト）

---

以上
