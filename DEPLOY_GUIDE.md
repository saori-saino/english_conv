# Streamlit Cloud デプロイメントガイド

## 問題の解決
`python-dotenv`の重複エラーが修正されました：
- 重複するバージョン指定を削除
- 必須パッケージのみに簡素化

## デプロイ手順

### 1. GitHubリポジトリの準備
```bash
git add .
git commit -m "Fix requirements.txt for Streamlit Cloud deployment"
git push origin main
```

### 2. Streamlit Cloudでの設定
1. [Streamlit Cloud](https://share.streamlit.io/)にアクセス
2. GitHubアカウントでログイン
3. 新しいアプリを作成:
   - Repository: `saori-saino/english_conv`
   - Branch: `main`
   - Main file path: `main.py`

### 3. Secrets設定
Streamlit Cloudのアプリ設定で以下を追加:
```toml
OPENAI_API_KEY = "your_openai_api_key_here"
```

### 4. 注意事項
- 音声録音機能はブラウザの制限により完全には動作しない可能性があります
- OpenAI APIキーは必ずSecrets経由で設定してください
- 初回デプロイ時は数分かかる場合があります

## トラブルシューティング
- デプロイエラーが発生した場合は、ログを確認してください
- 音声機能で問題が発生した場合は、テキスト入力モードを使用してください
