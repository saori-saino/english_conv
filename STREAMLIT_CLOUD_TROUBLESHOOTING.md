# Streamlit Cloud デプロイメント トラブルシューティング

## python-dotenvエラーが続く場合の対処法

### 🚨 現在のエラー
```
ERROR: Cannot install python-dotenv==1.0.0 and python-dotenv==1.0.1 because these package versions have conflicting dependencies.
```

### ✅ 解決策

#### 1. Streamlit Cloudでのキャッシュクリア
1. Streamlit Cloudアプリの設定画面に移動
2. "Reboot app"をクリック
3. または "Delete app" → 再作成

#### 2. 完全に固定バージョンを使用
現在の `requirements.txt` を以下に変更：

```
streamlit==1.41.1
openai==1.59.6
langchain==0.3.14
langchain-openai==0.3.0
python-dotenv==1.0.1
```

#### 3. 最小限のrequirements.txt
問題が続く場合は、さらに簡素化：

```
streamlit
openai
python-dotenv
```

#### 4. 代替手段: python-dotenvを削除
`.env`ファイルの代わりにStreamlit Secretsのみ使用：

```
streamlit>=1.41.1
openai>=1.59.6
langchain>=0.3.14
langchain-openai>=0.3.0
```

### 💡 推奨デプロイ手順
1. まず解決策4でデプロイ
2. Streamlit SecretsでOPENAI_API_KEYを設定
3. アプリが動作することを確認
4. 必要に応じて他のパッケージを追加
