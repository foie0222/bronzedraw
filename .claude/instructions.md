# プロジェクト固有の指示

## GitHub操作

- GitHub関連の操作（Issue、PR、ファイル取得など）は常にMCPツール（`mcp__github__*`）を使用すること
- WebFetchは使わない
- 例: `mcp__github__get_issue`, `mcp__github__get_pull_request`, `mcp__github__get_file_contents`

## ブランチ命名規則

- Issue対応時は `issue-{issue番号}` の形式でブランチを作成
- 例: `issue-7`, `issue-20`

## コミットメッセージ規則

- フォーマット: `prefix: #issue番号 修正内容`
- prefixの種類（参考: https://qiita.com/muranakar/items/20a7927ffa63a5ca226a）
  - `feat`: 新機能
  - `fix`: バグ修正
  - `docs`: ドキュメントのみの変更
  - `style`: コードの動作に影響しない変更（フォーマットなど）
  - `refactor`: リファクタリング
  - `test`: テストの追加・修正
  - `chore`: ビルドプロセスやツールの変更
- 例: `docs: #20 .claude/instructions.mdを追加`
- **重要**: Claudeの署名やCo-Authored-By行は含めない
