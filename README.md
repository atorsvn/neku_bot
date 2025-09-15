# neku_bot
Discord Waifu bot powered by local models for text generation, emotion analysis, and text-to-speech.

![NEKU](https://raw.githubusercontent.com/atorsvn/neku_bot/main/neku.gif)

## Install
* Ensure system packages `ffmpeg` and `sox` are installed.
* Create a `.env` file containing your Discord token, e.g. `DISCORD_TOKEN=XXXX`.
* Populate `config/bot_config.json` with desired persona information.
* Install the package and Python dependencies with `pip install .`.

## Usage
* Start the bot programmatically:
  ```python
  from nekubot import NekuBot

  NekuBot("config/bot_config.json").run()
  ```
* In Discord use `!neku <your text here>` to chat with the bot.

## Docker

An optional Docker image is provided for running the bot in isolation.

1. Build the image:
   ```bash
   docker build -t neku-bot .
   ```
2. Run the container, mounting the configuration and database directories:
   ```bash
   docker run --rm -v $(pwd)/config:/app/config -v $(pwd)/db:/app/db neku-bot
   ```

The bot token is read from the `.env` file and persona details from `config/bot_config.json`.

## Testing

Run `pytest -q` to execute the test suite.

## Development

The bot code is organized as a Python package under `nekubot/`:

* `fgk_bot.py` contains the Discord cog.
* `outworld.py` orchestrates text generation and audio synthesis.
* `context.py` handles SQLite-backed conversation history.
* `tts.py` provides a thin wrapper around the Kokoro text-to-speech pipeline.
* `media.py` assembles audio and video assets using temporary files to avoid
  manual cleanup.

This modular layout makes it easy to replace or extend individual components.

## Publishing

Build and upload the package to PyPI:

```bash
pip install build twine
python -m build
twine upload dist/*
```

Remember to bump the version in `pyproject.toml` and `nekubot/__init__.py` before releasing.
