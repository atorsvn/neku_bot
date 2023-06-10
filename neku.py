# Import necessary libraries
import discord
from discord.ext import commands
import re
import asyncio
import random
import os
import logging

# Import the FGKBot module
from fgk_neku import FGKBot

# This function sets up the logging system with a specific format and error level
def setup_logging():
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# This function creates a new Bot instance with default intents and a specific command prefix
def setup_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    return commands.Bot(command_prefix='!', intents=intents)

# This event is triggered when the bot is ready. It logs the bot username.
@bot.event
async def on_ready():
    try:
        print('We have logged in as {0.user}'.format(bot))
    except Exception as e:
        logging.error(f"Error in on_ready: {e}")

# This function wraps the avatar_waifu method from the FGKBot class
async def run_avatar_waifu(ctx, query):
    try:
        await future_gadget_kr3w.avatar_waifu(ctx, query, ctx.message.author.name, ctx.message.author.id, ctx.message.channel.id)
    except Exception as e:
        logging.error(f"Error in neku command: {e}")

# This command wraps the above function with typing status and error handling
@bot.command(name='neku')
async def neku(ctx, *, query=""):
    try:
        if ctx.message.author == bot.user:
            return

        async with ctx.typing():
            asyncio.create_task(run_avatar_waifu(ctx, query))
    except Exception as e:
        logging.error(f"Error in neku command: {e}")

# This is the main function that initializes logging, the bot, and the event loop
def main():
    try:
        setup_logging()
        bot = setup_bot()

        future_gadget_kr3w = FGKBot(bot)
        
        loop = asyncio.get_event_loop()
        loop.create_task(bot.start(future_gadget_kr3w.BOT_CONFIG['DISCORD-TOKEN']))
        loop.run_forever()
    except Exception as e:
        logging.error(f"Error running bot: {e}")

# This makes sure the main function is called when the script is run directly
if __name__ == "__main__":
    main()
