"""Entry point for running the Neku Discord bot."""

from nekubot import NekuBot


def main() -> None:
    """Instantiate the bot using the default configuration."""
    NekuBot("config/bot_config.json").run()


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()

