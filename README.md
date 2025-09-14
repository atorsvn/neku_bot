# neku_bot
Discord Waifu bot powered by local models for text generation, emotion analysis, and text-to-speech.

![NEKU](https://raw.githubusercontent.com/atorsvn/neku_bot/main/neku.gif)

## Install
* Populate `config/bot_config.json` with your Discord bot token and desired persona information.
* Install dependencies with `pip install -r requirements.txt`.
## Usage
* Run `python neku.py` to start the bot. The entry script configures logging and
  launches the Discord client using `asyncio.run`.
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

The bot token and persona are read from `config/bot_config.json`.

## Testing

Run `pytest -q` to execute the test suite.
