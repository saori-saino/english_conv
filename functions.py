import streamlit as st
import os
import time
from pathlib import Path
# import wave  # PyAudio関連なので不要
# import pyaudio  # PyAudioを無効化
# from pydub import AudioSegment  # pyaudioopエラーを回避するため無効化
# from audiorecorder import audiorecorder  # pyaudioopエラーを回避するため無効化
import numpy as np
# from scipy.io.wavfile import write  # 未使用のため無効化
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
import constants as ct

def record_audio(audio_input_file_path):
    """
    音声入力を受け取って音声ファイルを作成（Streamlit標準機能使用）
    """
    
    st.subheader("🎤 音声入力")
    
    # Streamlitの標準音声入力を使用
    audio_bytes = st.audio_input("音声を録音してください")
    
    if audio_bytes is not None:
        # 音声ファイルを保存
        with open(audio_input_file_path, "wb") as f:
            f.write(audio_bytes.getvalue())
        
        st.success("音声が正常に録音されました！")
        return True
    else:
        st.info("音声を録音してください。")
        return False

def transcribe_audio(audio_input_file_path):
    """
    音声入力ファイルから文字起こしテキストを取得
    Args:
        audio_input_file_path: 音声入力ファイルのパス
    """

    with open(audio_input_file_path, 'rb') as audio_input_file:
        transcript = st.session_state.openai_obj.audio.transcriptions.create(
            model="whisper-1",
            file=audio_input_file,
            language="en"
        )
    
    # 音声入力ファイルを削除
    os.remove(audio_input_file_path)

    return transcript

def save_to_wav(llm_response_audio, audio_output_file_path):
    """
    音声データを直接mp3ファイルとして保存（pydub不使用版）
    Args:
        llm_response_audio: LLMからの回答の音声データ
        audio_output_file_path: 出力先のファイルパス
    """

    # OpenAIのTTSはmp3形式で出力されるため、直接mp3として保存
    mp3_file_path = audio_output_file_path.replace('.wav', '.mp3')
    
    try:
        with open(mp3_file_path, "wb") as audio_output_file:
            audio_output_file.write(llm_response_audio)
        return mp3_file_path  # 実際に保存されたファイルパスを返す
    except Exception as e:
        st.error(f"音声ファイルの保存に失敗しました: {e}")
        raise

def play_wav(audio_output_file_path, speed=1.0):
    """
    音声ファイルの再生（手動再生推奨）
    Args:
        audio_output_file_path: 音声ファイルのパス
        speed: 再生速度（現在は無効、pydub不使用のため）
    """
    
    # 速度変更機能の案内
    if speed != 1.0:
        st.warning(f"⚠️ 音声速度変更機能は現在無効になっています（指定速度: {speed}x）")
    
    # ユーザーに明確な操作指示を表示
    st.success("🎵 **問題文の音声が生成されました！**")
    st.info("👇 **下の音声プレーヤーで ▶️ ボタンを押して問題文を聞いてください**")
    
    # Streamlitの音声再生機能を使用
    try:
        with open(audio_output_file_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            
            # 手動再生のみ（autoplay=Falseに変更）
            if audio_output_file_path.endswith('.mp3'):
                st.audio(audio_bytes, format='audio/mp3', autoplay=False)
            else:
                st.audio(audio_bytes, format='audio/wav', autoplay=False)
            
            # 追加の案内メッセージ
            st.markdown("""
            � **音声が聞こえない場合:**
            - 音声プレーヤーの ▶️ ボタンを手動でクリックしてください
            - ブラウザの音量設定を確認してください
            - スピーカーまたはヘッドフォンの接続を確認してください
            """)
            
    except Exception as e:
        st.error(f"🚨 音声ファイルの準備に失敗しました: {e}")
        st.info("音声が利用できませんが、テキストでの問題文は生成されています。")
        return
    
    # 音声ファイルは即座に削除せず、セッション終了時まで保持
    # （ユーザーが複数回再生できるようにするため）
    
    # 音声ファイルを削除（一定時間後）
    try:
        # 即座に削除せず、少し待つ（音声再生のため）
        # os.remove(audio_output_file_path)  # 音声再生完了後まで削除を延期
        pass
    except Exception as e:
        st.warning(f"音声ファイルの削除に失敗しました: {e}")

def create_chain(system_template):
    """
    LLMによる回答生成用のChain作成
    """

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_template),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}")
    ])
    chain = ConversationChain(
        llm=st.session_state.llm,
        memory=st.session_state.memory,
        prompt=prompt
    )

    return chain

def create_problem_and_play_audio():
    """
    問題生成と音声ファイルの再生
    Args:
        chain: 問題文生成用のChain
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
        openai_obj: OpenAIのオブジェクト
    """

    # 問題文を生成するChainを実行し、問題文を取得
    problem = st.session_state.chain_create_problem.predict(input="")

    # LLMからの回答を音声データに変換
    llm_response_audio = st.session_state.openai_obj.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=problem
    )

    # 音声ファイルの作成（mp3形式で保存）
    audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.mp3"
    actual_file_path = save_to_wav(llm_response_audio.content, audio_output_file_path)

    # ディクテーション用の追加UI表示
    st.markdown("### 📝 ディクテーション問題")
    st.info("🎧 **音声を聞いて、聞こえた内容を正確に入力してください**")
    
    # 音声ファイルの読み上げ
    play_wav(actual_file_path, st.session_state.speed)

    return problem, llm_response_audio

def create_evaluation():
    """
    ユーザー入力値の評価生成
    """

    llm_response_evaluation = st.session_state.chain_evaluation.predict(input="")

    return llm_response_evaluation

# LangChain代替関数（Pydantic互換性問題の回避用）
def create_simple_openai_client(api_key):
    """
    単純なOpenAI APIクライアントを作成（LangChain代替）
    """
    from openai import OpenAI
    return OpenAI(api_key=api_key)

def simple_chat_completion(client, messages, model="gpt-4o-mini", temperature=0.5):
    """
    OpenAI API直接呼び出しでチャット補完（LangChain代替）
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API呼び出しエラー: {e}"

def create_conversation_messages(system_prompt, conversation_history, user_input):
    """
    会話履歴から OpenAI API用のメッセージ形式を作成
    """
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # 会話履歴を追加
    for msg in conversation_history:
        if hasattr(msg, 'content'):
            role = "assistant" if hasattr(msg, 'type') and msg.type == "ai" else "user"
            messages.append({"role": role, "content": msg.content})
    
    # 現在のユーザー入力を追加
    messages.append({"role": "user", "content": user_input})
    
    return messages