import streamlit as st
import os
import time
from time import sleep
from pathlib import Path
from streamlit.components.v1 import html
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from openai import OpenAI
from langchain_openai import ChatOpenAI
# Streamlit Cloud対応：python-dotenvの代わりにStreamlit Secretsを使用
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
import functions as ft
import constants as ct

# Pydantic互換性の問題を解決
try:
    # ChatOpenAIクラスのモデル再構築を強制実行
    from langchain_core.language_models.base import BaseLanguageModel
    ChatOpenAI.model_rebuild()
except Exception as e:
    print(f"Warning: ChatOpenAI model rebuild failed: {e}")
    # 継続して実行


# 各種設定
# .envファイルを明示的に読み込み（ローカル環境のみ）
if DOTENV_AVAILABLE:
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path, override=True)

# API key の設定（Streamlit Cloud + ローカル対応）
def get_openai_api_key():
    # 1. Streamlit Secrets
    try:
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            return st.secrets['OPENAI_API_KEY']
    except Exception:
        pass
    
    # 2. 環境変数
    if "OPENAI_API_KEY" in os.environ:
        return os.environ["OPENAI_API_KEY"]
    
    # 3. .envファイル（ローカル開発用）
    if DOTENV_AVAILABLE:
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENAI_API_KEY=') and not line.startswith('#'):
                        key_value = line.split('=', 1)
                        if len(key_value) == 2:
                            return key_value[1].strip('"\'')
    
    return None

# OpenAI API key の設定
api_key = get_openai_api_key()
if api_key:
    os.environ['OPENAI_API_KEY'] = api_key

st.set_page_config(
    page_title=ct.APP_NAME
)

# タイトル表示
st.markdown(f"## {ct.APP_NAME}")

# 初期処理
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.start_flg = False
    st.session_state.pre_mode = ""
    st.session_state.shadowing_flg = False
    st.session_state.shadowing_button_flg = False
    st.session_state.shadowing_count = 0
    st.session_state.shadowing_first_flg = True
    st.session_state.shadowing_audio_input_flg = False
    st.session_state.shadowing_evaluation_first_flg = True
    st.session_state.dictation_flg = False
    st.session_state.dictation_button_flg = False
    st.session_state.dictation_count = 0
    st.session_state.dictation_first_flg = True
    st.session_state.dictation_chat_message = ""
    st.session_state.dictation_evaluation_first_flg = True
    st.session_state.chat_open_flg = False
    st.session_state.problem = ""
    st.session_state.audio_ready = False
    st.session_state.current_audio_file = None
    
    # OpenAI関連の初期化も一度だけ実行

# OpenAI API とLangChainの初期化（必要時のみ）
if "chain_basic_conversation" not in st.session_state:
    st.info("🔄 OpenAI APIとLangChainを初期化中...")
    
    # OpenAI APIキーの取得（複数の方法を試行）
    api_key = None
    
    # 方法1: 環境変数から直接取得
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # 方法2: .envファイルから手動読み込み
    if not api_key:
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('OPENAI_API_KEY=') and not line.startswith('#'):
                            key_value = line.split('=', 1)
                            if len(key_value) == 2:
                                api_key = key_value[1].strip('"\'')
                                os.environ['OPENAI_API_KEY'] = api_key
                                break
            except Exception as e:
                st.warning(f".envファイル読み込みエラー: {e}")
    
    # 方法3: Streamlit secretsから取得
    if not api_key:
        try:
            if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            pass
    
    # APIキーの検証
    if not api_key or api_key == "your-openai-api-key-here" or len(api_key) < 20:
        st.error("🔑 OpenAI APIキーが設定されていません。")
        st.info("""
        **APIキーの設定方法:**
        1. OpenAIのWebサイト (https://platform.openai.com/account/api-keys) でAPIキーを取得
        2. 以下のいずれかの方法で設定:
           - 環境変数: `OPENAI_API_KEY=your_key`
           - `.streamlit/secrets.toml` ファイルに追加
        """)
        st.stop()
    
    try:
        st.session_state.openai_obj = OpenAI(api_key=api_key)
        
        # ChatOpenAIの初期化 - 段階的に異なる方法を試行
        llm_initialized = False
        
        # 方法1: 基本的な初期化
        if not llm_initialized:
            try:
                st.session_state.llm = ChatOpenAI(
                    api_key=api_key,
                    model="gpt-4o-mini",
                    temperature=0.5
                )
                llm_initialized = True
                st.success("✅ ChatOpenAI初期化成功（方法1）")
            except Exception as e1:
                st.warning(f"方法1失敗: {e1}")
        
        # 方法2: openai_api_keyパラメータを使用
        if not llm_initialized:
            try:
                st.session_state.llm = ChatOpenAI(
                    openai_api_key=api_key,
                    model="gpt-4o-mini",
                    temperature=0.5
                )
                llm_initialized = True
                st.success("✅ ChatOpenAI初期化成功（方法2）")
            except Exception as e2:
                st.warning(f"方法2失敗: {e2}")
        
        # 方法3: 環境変数に依存する方法
        if not llm_initialized:
            try:
                os.environ['OPENAI_API_KEY'] = api_key
                st.session_state.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.5
                )
                llm_initialized = True
                st.success("✅ ChatOpenAI初期化成功（方法3）")
            except Exception as e3:
                st.warning(f"方法3失敗: {e3}")
        
        # 方法4: 旧形式のパラメータ名を使用
        if not llm_initialized:
            try:
                st.session_state.llm = ChatOpenAI(
                    openai_api_key=api_key,
                    model_name="gpt-4o-mini",
                    temperature=0.5
                )
                llm_initialized = True
                st.success("✅ ChatOpenAI初期化成功（方法4 - 旧形式）")
            except Exception as e4:
                st.warning(f"方法4失敗: {e4}")
        
        if not llm_initialized:
            raise Exception("すべてのChatOpenAI初期化方法が失敗しました")
        
        # LangChainのメモリとチェーンを初期化
        try:
            st.session_state.memory = ConversationSummaryBufferMemory(
                llm=st.session_state.llm,
                max_token_limit=1000,
                return_messages=True
            )

            # モード「日常英会話」用のChain作成
            st.session_state.chain_basic_conversation = ft.create_chain(ct.SYSTEM_TEMPLATE_BASIC_CONVERSATION)
            st.session_state.use_langchain = True
            st.success("✅ LangChainチェーン初期化成功")
            
        except Exception as chain_error:
            st.warning(f"⚠️ LangChainチェーン作成失敗、直接OpenAI API使用モードに切り替えます: {chain_error}")
            st.session_state.use_langchain = False
            st.session_state.conversation_history = []  # 代替の会話履歴管理
            
            # フォールバック用のダミーチェーンオブジェクトを作成
            class FallbackChain:
                def __init__(self, api_key):
                    self.api_key = api_key
                    self.client = ft.create_simple_openai_client(api_key)
                
                def predict(self, input):
                    try:
                        # シンプルな会話システムプロンプト
                        system_prompt = """あなたは優しく親切な英会話講師です。
ユーザーの英語に対して自然で適切な返答をしてください。
英語で返答し、発音しやすい文章を心がけてください。"""
                        
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": input}
                        ]
                        
                        return ft.simple_chat_completion(self.client, messages)
                    except Exception as e:
                        return f"申し訳ございません。応答の生成でエラーが発生しました: {e}"
            
            st.session_state.chain_basic_conversation = FallbackChain(api_key)
            st.info("✅ フォールバックモードで初期化完了")
        
    except Exception as e:
        st.error(f"🚨 OpenAI API初期化エラー: {e}")
        st.info("APIキーが正しく設定されているか確認してください。")
        st.stop()

# 初期表示
# col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
# 提出課題用
col1, col2, col3, col4 = st.columns([2, 2, 3, 3])
with col1:
    if st.session_state.start_flg:
        st.button("開始", use_container_width=True, type="primary")
    else:
        st.session_state.start_flg = st.button("開始", use_container_width=True, type="primary")
with col2:
    st.session_state.speed = st.selectbox(label="再生速度", options=ct.PLAY_SPEED_OPTION, index=3, label_visibility="collapsed")
with col3:
    st.session_state.mode = st.selectbox(label="モード", options=[ct.MODE_1, ct.MODE_2, ct.MODE_3], label_visibility="collapsed")
    # モードを変更した際の処理
    if st.session_state.mode != st.session_state.pre_mode:
        # 自動でそのモードの処理が実行されないようにする
        st.session_state.start_flg = False
        # 「日常英会話」選択時の初期化処理
        if st.session_state.mode == ct.MODE_1:
            st.session_state.dictation_flg = False
            st.session_state.shadowing_flg = False
        # 「シャドーイング」選択時の初期化処理
        st.session_state.shadowing_count = 0
        if st.session_state.mode == ct.MODE_2:
            st.session_state.dictation_flg = False
        # 「ディクテーション」選択時の初期化処理
        st.session_state.dictation_count = 0
        if st.session_state.mode == ct.MODE_3:
            st.session_state.shadowing_flg = False
        # チャット入力欄を非表示にする
        st.session_state.chat_open_flg = False
    st.session_state.pre_mode = st.session_state.mode
with col4:
    st.session_state.englv = st.selectbox(label="英語レベル", options=ct.ENGLISH_LEVEL_OPTION, label_visibility="collapsed")

with st.chat_message("assistant", avatar="images/ai_icon.jpg"):
    st.markdown("こちらは生成AIによる音声英会話の練習アプリです。何度も繰り返し練習し、英語力をアップさせましょう。")
    st.markdown("**【操作説明】**")
    st.success("""
    - モードと再生速度を選択し、「英会話開始」ボタンを押して英会話を始めましょう。
    - モードは「日常英会話」「シャドーイング」「ディクテーション」から選べます。
    - 発話後、5秒間沈黙することで音声入力が完了します。
    - 「一時中断」ボタンを押すことで、英会話を一時中断できます。
    """)
    
    # 日常英会話モード専用の音声ヘルプを常時表示
    if st.session_state.mode == ct.MODE_1:
        with st.expander("🔧 音声が聞こえない場合（日常英会話モード）"):
            st.markdown("""
            **ブラウザの自動再生が無効になっている可能性があります:**
            1. AI回答の音声プレーヤーで ▶️ ボタンを手動でクリックしてください
            2. ブラウザの設定で音声自動再生を許可してください
            3. 音量設定を確認してください
            
            **Chrome/Edge:** 設定 → プライバシーとセキュリティ → サイトの設定 → 音声
            **Firefox:** 設定 → プライバシーとセキュリティ → 許可設定 → 自動再生
            """)
st.divider()

# メッセージリストの一覧表示
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message(message["role"], avatar="images/ai_icon.jpg"):
            st.markdown(message["content"])
    elif message["role"] == "user":
        with st.chat_message(message["role"], avatar="images/user_icon.jpg"):
            st.markdown(message["content"])
    else:
        st.divider()

# LLMレスポンスの下部にモード実行のボタン表示
if st.session_state.shadowing_flg:
    st.session_state.shadowing_button_flg = st.button("シャドーイング開始")
if st.session_state.dictation_flg:
    st.session_state.dictation_button_flg = st.button("ディクテーション開始")

# 「ディクテーション」モードのチャット入力受付時に実行
if st.session_state.chat_open_flg:
    # 音声プレーヤーを表示（st.rerun()の影響を受けない場所）
    ft.display_audio_player()
    st.info("AIが読み上げた音声を、画面下部のチャット欄からそのまま入力・送信してください。")

st.session_state.dictation_chat_message = st.chat_input("※「ディクテーション」選択時以外は送信不可")

if st.session_state.dictation_chat_message and not st.session_state.chat_open_flg:
    st.stop()

# 「英会話開始」ボタンが押された場合の処理
if st.session_state.start_flg:

    # モード：「ディクテーション」
    # 「ディクテーション」ボタン押下時か、「英会話開始」ボタン押下時か、チャット送信時
    if st.session_state.mode == ct.MODE_3 and (st.session_state.dictation_button_flg or st.session_state.dictation_count == 0 or st.session_state.dictation_chat_message):
        if st.session_state.dictation_first_flg:
            st.session_state.chain_create_problem = ft.create_chain(ct.SYSTEM_TEMPLATE_CREATE_PROBLEM)
            st.session_state.dictation_first_flg = False
        # チャット入力以外
        if not st.session_state.chat_open_flg:
            with st.spinner('問題文生成中...'):
                st.session_state.problem, llm_response_audio = ft.create_problem_and_play_audio()

            st.session_state.chat_open_flg = True
            st.session_state.dictation_flg = False
            st.rerun()
        # チャット入力時の処理
        else:
            # チャット欄から入力された場合にのみ評価処理が実行されるようにする
            if not st.session_state.dictation_chat_message:
                st.stop()
            
            # AIメッセージとユーザーメッセージの画面表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(st.session_state.problem)
            with st.chat_message("user", avatar=ct.USER_ICON_PATH):
                st.markdown(st.session_state.dictation_chat_message)

            # LLMが生成した問題文とチャット入力値をメッセージリストに追加
            st.session_state.messages.append({"role": "assistant", "content": st.session_state.problem})
            st.session_state.messages.append({"role": "user", "content": st.session_state.dictation_chat_message})
            
            with st.spinner('評価結果の生成中...'):
                system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                    llm_text=st.session_state.problem,
                    user_text=st.session_state.dictation_chat_message
                )
                st.session_state.chain_evaluation = ft.create_chain(system_template)
                # 問題文と回答を比較し、評価結果の生成を指示するプロンプトを作成
                llm_response_evaluation = ft.create_evaluation()
            
            # 評価結果のメッセージリストへの追加と表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(llm_response_evaluation)
            st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
            st.session_state.messages.append({"role": "other"})
            
            # 各種フラグの更新
            st.session_state.dictation_flg = True
            st.session_state.dictation_chat_message = ""
            st.session_state.dictation_count += 1
            st.session_state.chat_open_flg = False

            st.rerun()

    
    # モード：「日常英会話」
    if st.session_state.mode == ct.MODE_1:
        # 音声入力を受け取って音声ファイルを作成
        audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        
        if ft.record_audio(audio_input_file_path):
            # 音声入力ファイルから文字起こしテキストを取得
            with st.spinner('音声入力をテキストに変換中...'):
                transcript = ft.transcribe_audio(audio_input_file_path)
                audio_input_text = transcript.text

            # 音声入力テキストの画面表示
            with st.chat_message("user", avatar=ct.USER_ICON_PATH):
                st.markdown(audio_input_text)

            with st.spinner("🤖 AI回答を生成中..."):
                # ユーザー入力値をLLMに渡して回答取得
                llm_response = st.session_state.chain_basic_conversation.predict(input=audio_input_text)
            
            with st.spinner("🎤 音声を生成中..."):
                # LLMからの回答を音声データに変換
                llm_response_audio = st.session_state.openai_obj.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=llm_response
            )

            # mp3形式で音声ファイル作成
            audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.mp3"
            actual_file_path = ft.save_to_wav(llm_response_audio.content, audio_output_file_path)

            # 音声ファイルの読み上げ（日常英会話モード専用自動再生）
            ft.play_wav_auto_for_conversation(actual_file_path, speed=st.session_state.speed)

            # AIメッセージの画面表示とリストへの追加
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(llm_response)

            # ユーザー入力値とLLMからの回答をメッセージ一覧に追加
            st.session_state.messages.append({"role": "user", "content": audio_input_text})
            st.session_state.messages.append({"role": "assistant", "content": llm_response})


    # モード：「シャドーイング」
    # 「シャドーイング」ボタン押下時か、「英会話開始」ボタン押下時
    if st.session_state.mode == ct.MODE_2 and (st.session_state.shadowing_button_flg or st.session_state.shadowing_count == 0 or st.session_state.shadowing_audio_input_flg):
        if st.session_state.shadowing_first_flg:
            st.session_state.chain_create_problem = ft.create_chain(ct.SYSTEM_TEMPLATE_CREATE_PROBLEM)
            st.session_state.shadowing_first_flg = False
        
        if not st.session_state.shadowing_audio_input_flg:
            with st.spinner('問題文生成中...'):
                st.session_state.problem, llm_response_audio = ft.create_problem_and_play_audio_for_shadowing()

        # 音声入力を受け取って音声ファイルを作成
        st.session_state.shadowing_audio_input_flg = True
        audio_input_file_path = f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        
        if ft.record_audio_for_shadowing(audio_input_file_path):
            st.session_state.shadowing_audio_input_flg = False

            with st.spinner('音声入力をテキストに変換中...'):
                # 音声入力ファイルから文字起こしテキストを取得
                transcript = ft.transcribe_audio(audio_input_file_path)
                audio_input_text = transcript.text

            # AIメッセージとユーザーメッセージの画面表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(st.session_state.problem)
            with st.chat_message("user", avatar=ct.USER_ICON_PATH):
                st.markdown(audio_input_text)
            
            # LLMが生成した問題文と音声入力値をメッセージリストに追加
            st.session_state.messages.append({"role": "assistant", "content": st.session_state.problem})
            st.session_state.messages.append({"role": "user", "content": audio_input_text})

            with st.spinner('評価結果の生成中...'):
                if st.session_state.shadowing_evaluation_first_flg:
                    system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                        llm_text=st.session_state.problem,
                        user_text=audio_input_text
                    )
                    st.session_state.chain_evaluation = ft.create_chain(system_template)
                    st.session_state.shadowing_evaluation_first_flg = False
                # 問題文と回答を比較し、評価結果の生成を指示するプロンプトを作成
                llm_response_evaluation = ft.create_evaluation()
            
            # 評価結果のメッセージリストへの追加と表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(llm_response_evaluation)
            st.session_state.messages.append({"role": "assistant", "content": llm_response_evaluation})
            st.session_state.messages.append({"role": "other"})
            
            # 各種フラグの更新
            st.session_state.shadowing_flg = True
            st.session_state.shadowing_count += 1

        # 「シャドーイング」ボタンを表示するために再描画
        st.rerun()