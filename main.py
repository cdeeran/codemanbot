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
from codemanbot import CodemanBot

# Load in the .env file
load_dotenv(".env")

# Constants from .env
TOKEN = os.environ.get("TOKEN")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
NICKNAME = os.environ.get("NICKNAME")
PREFIX = os.environ.get("PREFIX")
CHANNEL = os.environ.get("CHANNEL")


def main():
    """
    Entry point for the bot
    """
    # Initialize the bot
    codemanbot = CodemanBot(
        token=TOKEN,
        client_secret=CLIENT_SECRET,
        prefix=PREFIX,
        channels=[CHANNEL],
        nickname=NICKNAME,
        logging=True,
    )

    codemanbot.run()


if __name__ == "__main__":
    main()
