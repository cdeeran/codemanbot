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
    # "Merch": "https://merch.streamelements.com/therealcodeman",
    "Email": "dev@codydeeran.com",
}

import os
import sys
import asyncio
import discord
import config
from src.twitchbot import CodemanTwitchBot
from src.discordbot import CodemanDiscordBot
from src.spotify import SpotifyClient
from src.thread_manager import DiscordThread

BUNDLE_DIRECTORY = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
ASSETS_FILE_PATH = os.path.abspath(os.path.join(BUNDLE_DIRECTORY, "assets"))
PLAYER_OVERLAY_PATH = os.path.abspath(os.path.join(BUNDLE_DIRECTORY, "player_overlay"))


async def main():
    """
    Entry point for the bot
    """

    os.makedirs(config.LOGS_FILE_PATH, exist_ok=True)

    spotify_instance = SpotifyClient(
        device_name=config.SPOTIFY_PLAYBACK_DEVICE,
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect=config.SPOTIFY_REDIRECT,
        logging_path=config.LOGS_FILE_PATH,
        player_overlay_path=config.PLAYER_OVERLAY_PATH,
    )

    # Initialize the bot
    codeman_twitch_bot = CodemanTwitchBot(
        bot_name="therealcodemanbot",
        twitch_tmi_token=config.TWITCH_TMI_TOKEN,
        twitch_client_id=config.TWITCH_CLIENT_ID,
        twitch_client_secret=config.TWITCH_CLIENT_SECRET,
        prefix=config.PREFIX,
        channel={
            "name": config.CHANNEL,
            "url": config.CHANNEL_URL,
            "id": config.CHANNEL_ID,
        },
        spotify_instance=spotify_instance,
        weather_api_key=config.WEATHER_API_KEY,
        logging_path=config.LOGS_FILE_PATH,
        openai_key=config.OPENAI_API_KEY,
        logging=False,
    )

    discord_intents = discord.Intents.default()
    discord_intents.message_content = True
    codeman_discord_bot = CodemanDiscordBot(
        intents=discord_intents,
        twitch_url=config.CHANNEL_URL,
        twitch_channel=config.CHANNEL,
        notifications_channel_id=int(config.DISCORD_NOTIFICATION_CHANNEL_ID),
        assets=config.ASSETS_FILE_PATH,
        logging_path=config.LOGS_FILE_PATH,
    )

    discord_thread = DiscordThread(
        target=codeman_discord_bot.run, key=config.DISCORD_SECRET, name="Discord_Thread"
    )
    discord_thread.start()

    await asyncio.gather(
        codeman_twitch_bot.run(),
    )

    discord_thread.join()


if __name__ == "__main__":

    asyncio.run(main())
