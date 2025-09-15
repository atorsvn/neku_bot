import base64
import io
import json
import os
import sqlite3

import nltk
import soundfile as sf
from kokoro import KPipeline
from ollama import chat, ChatResponse
from transformers import pipeline

from nekubot.context import ContextStore
from nekubot.tts import KokoroTTS

nltk.download("punkt")

MAX_CONTEXT_HISTORY = 8


class OutworldGenerator:
    """Generate responses and audio using local models."""

    def __init__(
        self,
        model: str = "llama3.2",
        lang_code: str = "a",
        voice: str = "af_heart",
        speed: int = 1,
        config: dict | None = None,
        config_path: str = "bot_config.json",
        db_path: str = "context_history.db",
    ) -> None:
        self.model = model
        self.tts = KokoroTTS(lang_code=lang_code, voice=voice, speed=speed)
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice
        self.speed = speed

        if config is None:
            if not os.path.exists(config_path):
                raise FileNotFoundError(
                    f"Configuration file {config_path} not found."
                )
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        self.config = config

        self.context = ContextStore(db_path)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS context_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

        self.emotion_classifier = pipeline(
            "text-classification",
            model="bhadresh-savani/distilbert-base-uncased-emotion",
            return_all_scores=True,
        )

    def save_message(self, user_id: str, role: str, content: str) -> None:
        self.context.save_message(user_id, role, content)
        self.cursor.execute(
            "INSERT INTO context_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        self.conn.commit()

    def get_context(self, user_id: str):
        self.cursor.execute(
            "SELECT role, content FROM context_history WHERE user_id = ? ORDER BY timestamp ASC",
            (user_id,),
        )
        rows = self.cursor.fetchall()
        context = [{"role": row[0], "content": row[1]} for row in rows]
        if len(context) > MAX_CONTEXT_HISTORY:
            context = context[-MAX_CONTEXT_HISTORY:]
        return self.context.get_context(user_id)

    def chat_ollama(self, user_id: str, user_prompt: str) -> str:
        system_prompt = (
            f"Bot Name: {self.config.get('bot_name', 'Bot')}\n"
            f"Prompt: {self.config.get('bot_prompt', '')}\n"
            f"Personality: {self.config.get('bot_personality', '')}\n"
            f"Situation: {self.config.get('bot_situation', '')}\n"
        )

        context_messages = self.get_context(user_id)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context_messages)
        messages.append({"role": "user", "content": user_prompt})

        self.save_message(user_id, "user", user_prompt)

        response: ChatResponse = chat(model=self.model, messages=messages)
        assistant_response = response.message.content
        self.save_