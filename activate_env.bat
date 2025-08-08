@echo off
echo 生成AI英会話アプリ専用の仮想環境をアクティベートしています...
call ai_english_app_env\Scripts\activate.bat
echo.
echo 仮想環境がアクティベートされました！
echo Streamlitアプリを起動するには以下のコマンドを実行してください:
echo python -m streamlit run main.py
echo.
echo 仮想環境を無効化するには 'deactivate' と入力してください。
echo.
cmd /k
