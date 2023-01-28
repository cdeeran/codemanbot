# cspell: disable
"""
codemanbot.py: Interface with the Twitch chat via twitchio API.
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

import json
from datetime import datetime
import emoji
from twitchio.ext import commands
from twitchio.message import Message


class CodemanBot(commands.Bot):
    """
    Twitch bot for therealcodeman

    https://twitch.tv/therealcodeman
    """

    def __init__(
        self,
        token: str,
        client_secret: str,
        prefix: str,
        channels: list[str],
        nickname: str,
        logging: bool = False,
    ) -> None:

        # Initialize the bot
        super().__init__(
            token=token,
            client_secret=client_secret,
            prefix=prefix,
            initial_channels=channels,
        )

        self.nickname = nickname
        self.session_deaths: int = 0
        self.lifetime_deaths: int = 0
        self.session_chalked: int = 0
        self.lifetime_chalked: int = 0
        self.recent_raffle: bool = False
        self.raffle_time: datetime = None
        self.raffle_cooldown_time: int = 15  # minutes
        self.logging: bool = logging
        self.session_log = f"session_{datetime.now().strftime('%d-%m-%y-%H-%M-%S')}.log"

    async def event_ready(self):
        """Initialize the bot"""

        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        self.lifetime_deaths = data["deaths"]
        self.lifetime_chalked = data["chalked"]

        print(emoji.emojize(f"{self.nick} is up and running! :robot:"))

    async def event_message(self, message: Message):
        """
        Read in message from chat

        Args:
            message (Message): Message from Twitch chat
        """
        # Messages with echo set to True are messages sent by the bot.
        # Ignore them
        if message.echo:
            return

        if self.logging:
            with open(f"./.logs/{self.session_log}", "a+", encoding="utf-8") as log:
                log.write(f"{message.author.name}: {message.content}\n\n")

        # relay message
        await self.handle_commands(message)

    @commands.command(name="hello")
    async def hello(self, context: commands.Context):
        """
        Return a hello to the user

        Args:
            context (commands.Context): Context Object
        """
        await context.reply(f"Hello {context.author.name}!")

    @commands.command(name="raffle")
    async def raffle(self, context: commands.Context):
        """
        Return a hello to the user

        Args:
            context (commands.Context): Context Object
        """
        current_time = datetime.now()

        if self.recent_raffle:

            elapsed_time = (current_time - self.raffle_time).total_seconds() // 60

            print(f"Elapsed Time: {elapsed_time}")

            if elapsed_time >= self.raffle_cooldown_time:
                await context.send(emoji.emojize("Okay! Let's do a raffle! :ticket:"))
                await context.send("!raffle")
                self.raffle_time = datetime.now()
                self.recent_raffle = True
            else:
                await context.send(
                    f"I am sorry, @{context.author.name}"
                    "raffle is currently in cool down for another"
                    f"{self.raffle_cooldown_time - elapsed_time} minute(s).",
                )
        else:
            await context.send("Okay! Let's do a raffle! :ticket:")
            await context.send("!raffle")
            self.raffle_time = datetime.now()
            self.recent_raffle = True

    @commands.command(name="died", aliases=["dead"])
    async def died(self, context: commands.Context):
        """
        Update the death stats

        Args:
            context (commands.Context): Context Object
        """
        self.session_deaths += 1
        self.lifetime_deaths += 1

        with open("data.json", "r+", encoding="utf-8") as file:
            data = json.load(file)
            data["deaths"] = self.lifetime_deaths
            file.write(json.dumps(data, indent=4))

        await context.send(
            emoji.emojize(
                f":skull: @{self.connected_channels[0]} has died "
                f"{self.session_deaths} time(s) this session and "
                f"{self.lifetime_deaths} times in his career.",
            )
        )

    @commands.command(name="chalked")
    async def chalked(self, context: commands.Context):
        """
        Update the chalked stats

        Args:
            context (commands.Context): Context Object
        """
        self.session_chalked += 1
        self.lifetime_chalked += 1

        with open("data.json", "r+", encoding="utf-8") as file:
            data = json.load(file)
            data["chalked"] = self.lifetime_chalked
            file.write(json.dumps(data, indent=4))

        await context.send(
            f":speech_balloon: @{self.connected_channels[0]} said "
            f"`I'm chalked` {self.session_chalked}"
            f"time(s) this session and {self.lifetime_chalked} times in his career.",
        )

    @commands.command(name="guscam")
    async def guscam(self, context: commands.Context):
        """
        Send the message to show the Gus Cam.

        Args:
            context (commands.Context): Context Object
        """
        await context.send(
            emoji.emojize(
                ":dog: :wolf: GIVE THE PEOPLE WHAT THEY WANT! "
                "GUUUUUUS CAAAAAAAAM!!!!!!!! :dog: :wolf:"
            )
        )
