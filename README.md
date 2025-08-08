# 生成AI英会話アプリ

このプロジェクト専用の仮想環境を使用した英会話練習アプリです。

## セットアップ

### 1. 仮想環境のアクティベート

#### Windowsの場合:
```cmd
ai_english_app_env\Scripts\activate.bat
```

または、便利なバッチファイルを使用:
```cmd
activate_env.bat
```

#### 手動でアクティベートする場合:
```cmd
cd "プロジェクトフォルダのパス"
ai_english_app_env\Scripts\activate
```

### 2. 必要なパッケージのインストール

仮想環境をアクティベート後:
```cmd
pip install -r requirements.txt
```

### 3. アプリケーションの実行

```cmd
python -m streamlit run main.py
```

## 仮想環境について

- **仮想環境名**: `ai_english_app_env`
- **Python バージョン**: 3.13.5
- **目的**: このプロジェクト専用の独立した環境
- **利点**: 他のプロジェクトのパッケージと競合しない

## 使用方法

1. `activate_env.bat` をダブルクリックして仮想環境をアクティベート
2. `python -m streamlit run main.py` でアプリを起動
3. ブラウザでアプリが開かれます

## 仮想環境の無効化

```cmd
deactivate
```

## 注意事項

- 必ず仮想環境をアクティベートしてからアプリを実行してください
- 他のプロジェクトでこの仮想環境を使用しないでください
- 環境変数は `.env` ファイルで管理されています
