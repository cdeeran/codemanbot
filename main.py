# cspell: disable
"""
main.py: Main program for this project
"""
__author__ = "Cody Deeran"
__copyright__ = "Copyright 2023, codemanbot"
__license__ = "BSD 3-Clause License"
__version__ = "1.0"
__contact__ = {
    "Twitch": "https://twitch.tv/therealcodeman",
    "Youtube": "https://youtube.com/therealcodeman",
    "Twitter": "https://twitter.com/therealcodeman_",
    "Discord": "https://discord.gg/BW34FuYfnK",
    "Email": "dev@codydeeran.com",
}

import os
from dotenv import load_dotenv
import discord
from src.twitchbot import TwitchBot
from src.discordbot import DiscordBot
from src.botthread import BotThread

# Load in the .env file
load_dotenv(".env")

# Constants from .env
TOKEN = os.environ.get("TOKEN")
CLIENT_ID = os.environ.get("CLIENT_ID")
NICKNAME = os.environ.get("NICKNAME")
PREFIX = os.environ.get("PREFIX")
CHANNEL = os.environ.get("CHANNEL")
CHANNEL_URL = os.environ.get("CHANNEL_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DISCORD_SECRET = os.environ.get("DISCORD_SECRET")
DISCORD_NOTIFICATION_CHANNEL_ID = os.environ.get("DISCORD_NOTIFICATION_CHANNEL_ID")
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT = os.environ.get("SPOTIFY_REDIRECT")
SPOTIFY_PLAYBACK_DEVICE = os.environ.get("SPOTIFY_PLAYBACK_DEVICE")


def main():
    """
    Entry point for the bot
    """

    # Initialize the bot
    twitch_bot = TwitchBot(
        token=TOKEN,
        client_id=CLIENT_ID,
        prefix=PREFIX,
        channels=[CHANNEL],
        spotify_client_id=SPOTIFY_CLIENT_ID,
        spotify_client_secret=SPOTIFY_CLIENT_SECRET,
        spotify_device_name=SPOTIFY_PLAYBACK_DEVICE,
        spotify_redirect=SPOTIFY_REDIRECT,
        openai_key=OPENAI_API_KEY,
        logging=False,
    )

    discord_intents = discord.Intents.default()
    discord_intents.message_content = True
    discord_bot = DiscordBot(
        intents=discord_intents,
        twitch_url=CHANNEL_URL,
        twitch_channel=CHANNEL,
        notifications_channel_id=int(DISCORD_NOTIFICATION_CHANNEL_ID),
    )

    twitch_thread = BotThread(name="Twitch Bot", target=twitch_bot.run)
    discord_thread = BotThread(
        name="Discord Bot", target=discord_bot.run, key=DISCORD_SECRET
    )

    twitch_thread.start()
    discord_thread.start()
    twitch_thread.join()
    discord_thread.join()


if __name__ == "__main__":

    main()
