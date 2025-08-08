import streamlit as st
import os
import time
from pathlib import Path
# import wave  # PyAudio関連なので不要
# import pyaudio  # PyAudioを無効化
# from pydub import AudioSegment  # pyaudioopエラーを回避するため無効化
from audiorecorder import audiorecorder
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
    音声入力を受け取って音声ファイルを作成
    """

    audio = audiorecorder(
        start_prompt="発話開始",
        pause_prompt="やり直す",
        stop_prompt="発話終了",
        start_style={"color":"white", "background-color":"black"},
        pause_style={"color":"gray", "background-color":"white"},
        stop_style={"color":"white", "background-color":"black"}
    )

    if len(audio) > 0:
        audio.export(audio_input_file_path, format="wav")
    else:
        st.stop()

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
    音声ファイルの読み上げ（Streamlit使用、pydub不使用版）
    Args:
        audio_output_file_path: 音声ファイルのパス
        speed: 再生速度（現在は無効、pydub不使用のため）
    """
    
    # 速度変更機能は現在無効（pydub不使用のため）
    if speed != 1.0:
        st.info(f"音声速度変更機能は現在無効になっています（指定速度: {speed}x）")
    
    # Streamlitの音声再生機能を使用
    try:
        with open(audio_output_file_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            # ファイル拡張子に基づいてフォーマットを決定
            if audio_output_file_path.endswith('.mp3'):
                st.audio(audio_bytes, format='audio/mp3', autoplay=True)
            else:
                st.audio(audio_bytes, format='audio/wav', autoplay=True)
    except Exception as e:
        st.error(f"音声ファイルの再生に失敗しました: {e}")
    
    # 音声ファイルを削除
    try:
        os.remove(audio_output_file_path)
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

    # 音声ファイルの作成
    audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
    save_to_wav(llm_response_audio.content, audio_output_file_path)

    # 音声ファイルの読み上げ
    play_wav(audio_output_file_path, st.session_state.speed)

    return problem, llm_response_audio

def create_evaluation():
    """
    ユーザー入力値の評価生成
    """

    llm_response_evaluation = st.session_state.chain_evaluation.predict(input="")

    return llm_response_evaluation