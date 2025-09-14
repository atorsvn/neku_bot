import base64
import io

import soundfile as sf
import nltk
from kokoro import KPipeline


def ensure_tokenizer() -> None:
    """Ensure the punkt tokenizer is available for sentence splitting."""
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:  # pragma: no cover - one-time setup
        nltk.download("punkt")


class KokoroTTS:
    """Thin wrapper around Kokoro's text-to-speech pipeline."""

    def __init__(self, lang_code: str = "a", voice: str = "af_heart", speed: int = 1) -> None:
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice
        self.speed = speed

    def text_to_audio(self, text: str):
        """Convert ``text`` into segmented audio data structures."""
        ensure_tokenizer()
        sentences = nltk.sent_tokenize(text)
        audio_data_list = []
        idx = 0
        for sentence in sentences:
            generator = self.pipeline(
                sentence,
                voice=self.voice,
                speed=self.speed,
                split_pattern=None,
            )
            for _, (gs, ps, audio) in enumerate(generator):
                with io.BytesIO() as buffer:
                    sf.write(buffer, audio, 24000, format="WAV")
                    base64_audio = base64.b64encode(buffer.getvalue()).decode("utf-8")
                audio_data_list.append(
                    {
                        "index": idx,
                        "text": gs,
                        "phonemes": ps,
                        "audio_base64": base64_audio,
                    }
                )
                idx += 1
        return audio_data_list
