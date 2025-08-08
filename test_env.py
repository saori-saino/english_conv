#!/usr/bin/env python
"""
.envファイルのAPIキー読み込みテスト
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=== OpenAI APIキー読み込みテスト ===")

# 現在の作業ディレクトリを確認
print(f"現在のディレクトリ: {os.getcwd()}")

# .envファイルの存在確認
env_file = Path(".env")
print(f".envファイル存在: {env_file.exists()}")

if env_file.exists():
    print(f".envファイルパス: {env_file.absolute()}")
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f".envファイルサイズ: {len(content)} bytes")
        if "OPENAI_API_KEY" in content:
            print("✅ .envファイル内にOPENAI_API_KEYが見つかりました")
        else:
            print("❌ .envファイル内にOPENAI_API_KEYが見つかりません")

# python-dotenvで読み込みテスト
print("\n--- python-dotenv読み込みテスト ---")
result = load_dotenv(override=True)
print(f"load_dotenv結果: {result}")

# 環境変数の確認
if "OPENAI_API_KEY" in os.environ:
    key = os.environ["OPENAI_API_KEY"]
    print(f"✅ 環境変数にOPENAI_API_KEYが設定されています (長さ: {len(key)})")
    print(f"キーの先頭: {key[:20]}...")
else:
    print("❌ 環境変数にOPENAI_API_KEYが設定されていません")

# 手動読み込みテスト
print("\n--- 手動読み込みテスト ---")
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line.startswith('OPENAI_API_KEY='):
                key_value = line.split('=', 1)
                if len(key_value) == 2:
                    manual_key = key_value[1].strip('"\'')
                    print(f"✅ 手動読み込み成功 (行{line_num}): 長さ {len(manual_key)}")
                    print(f"手動キーの先頭: {manual_key[:20]}...")
                    os.environ['OPENAI_API_KEY'] = manual_key
                break

print("\n=== テスト完了 ===")
