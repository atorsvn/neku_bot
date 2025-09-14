import json
import os

from ollama import chat, ChatResponse
from transformers import pipeline
from nekubot.context import ContextStore
from nekubot.tts import KokoroTTS


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

        if config is None:
            if not os.path.exists(config_path):
                raise FileNotFoundError(
                    f"Configuration file {config_path} not found."
                )
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        self.config = config

        self.context = ContextStore(db_path)

        self.emotion_classifier = pipeline(
            "text-classification",
            model="bhadresh-savani/distilbert-base-uncased-emotion",
            return_all_scores=True,
        )

    def save_message(self, user_id: str, role: str, content: str) -> None:
        self.context.save_message(user_id, role, content)

    def get_context(self, user_id: str):
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
        self.save_message(user_id, "assistant", assistant_response)
        return assistant_response

    def generate_audio(self, text: str):
        return self.tts.text_to_audio(text)

    def run(self, user_id: str, user_prompt: str):
        response_text = self.chat_ollama(user_id, user_prompt)

        all_predictions = self.emotion_classifier(
            response_text, truncation=True, max_length=512
        )
        top_emotion = max(all_predictions[0], key=lambda x: x["score"])

        audio_data = self.generate_audio(response_text)

        return {"emotion": top_emotion, "audio_data": audio_data}
