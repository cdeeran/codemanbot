# cspell: disable
"""
discordbot.py: Interface with Discord via the discord api
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

from typing import Any
from discord import Client
from discord import Intents
from discord import Message
from discord import Embed
from discord import File
import emoji


class DiscordBot(Client):
    """
    Discord Bot

    Args:
        Client (_type_): Inherits discord.Client
    """

    def __init__(
        self,
        *,
        intents: Intents,
        twitch_url: str = None,
        twitch_channel: str = None,
        notifications_channel_id: int = -1,
        **options: Any,
    ) -> None:
        super().__init__(intents=intents, **options)
        self.twitch_url: str = twitch_url
        self.twitch_channel: str = twitch_channel
        self.notifications_channel_id: int = notifications_channel_id

    async def on_ready(self):
        """
        Print that the bot is up and running
        """
        print(f"{self.user} is now running!")

    async def on_message(self, message: Message):
        """
        Discord message to process

        Args:
            message (Message): discord.Message Object
        """

        message_content = message.content.lower()

        if message.author == self.user:
            return

        if message.content in [
            "hello",
            "hi",
            "sup",
            "what's up",
            "whats up",
            "what up",
            "wat up",
            "yo",
        ]:
            await message.channel.send(f"Hello! {message.author.mention}")
        elif message_content == "!help":
            await message.author.send("test")

        elif (
            message.content.startswith("!live")
            and message.author.id == 739002023755644999
        ):
            message.content = message.content.strip("!live").strip()
            await self.post_twitch_message(message)
        elif (
            message.content.startswith("!live")
            and message.author.id != 739002023755644999
        ):
            await message.channel.send(
                f"{message.author.mention} you don't have permission for the '!live' command."
            )
        else:
            return

    async def post_twitch_message(self, message: Message) -> None:
        """
        Post the 'going live' message to the notificaitons channel

        Args:
            message (Message): discord.Message Object
        """

        # Channel ID can be found by right clicking on the channel and
        # clicking on the option to 'Copy ID'
        notifications_channel = self.get_channel(self.notifications_channel_id)

        if notifications_channel:
            notification = emoji.emojize(
                f"@everyone\n\n**{message.author.mention} is LIVE on TWITCH! "
                + ":video_camera: :red_circle: :video_game:**\n\n"
                + "**WATCH :eyes:**\n\n"
            )

            image_file = File("./assets/brand-logo.png", filename="brand-logo.png")
            link_embed = Embed(
                title=self.twitch_channel,
                url=self.twitch_url,
                description=message.content,
            )
            link_embed.set_thumbnail(url="attachment://brand-logo.png")

            await notifications_channel.send(
                notification, file=image_file, embed=link_embed
            )
        else:
            await message.channel.send(
                f"Error: ({self.notifications_channel_id}) is an invalid channel id."
            )
