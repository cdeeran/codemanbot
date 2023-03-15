# cspell: disable
"""
twitchbot.py: Interface with the Twitch chat via twitchio API.
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
    "Merch": "https://merch.streamelements.com/therealcodeman",
    "Email": "dev@codydeeran.com",
}

import json
from datetime import datetime
import random
from queue import Queue
import emoji
import openai
import requests
from twitchio.ext import commands, routines
from twitchio.message import Message
from twitchio.errors import InvalidContent
from .spotify import Spotify, SpotifyReturnCode

EIGHT_BALL_REPSONSES = [
    emoji.emojize(":green_circle: It is certain."),
    emoji.emojize(":green_circle: It is decidedly so."),
    emoji.emojize(":green_circle: Without a doubt."),
    emoji.emojize(":green_circle: Yes definitely."),
    emoji.emojize(":green_circle: You may rely on it."),
    emoji.emojize(":green_circle: As I see it, yes."),
    emoji.emojize(":green_circle: Most likely."),
    emoji.emojize(":green_circle: Outlook good."),
    emoji.emojize(":green_circle: Yes."),
    emoji.emojize(":green_circle: Signs point to yes."),
    emoji.emojize(":yellow_circle: Reply hazy, try again."),
    emoji.emojize(":yellow_circle: Ask again later."),
    emoji.emojize(":yellow_circle: Better not tell you now."),
    emoji.emojize(":yellow_circle: Cannot predict now."),
    emoji.emojize(":yellow_circle: Concentrate and ask again."),
    emoji.emojize(":red_cricle: Don't count on it."),
    emoji.emojize(":red_cricle: My reply is no."),
    emoji.emojize(":red_cricle: My sources say no."),
    emoji.emojize(":red_cricle: Outlook not so good."),
    emoji.emojize(":red_cricle: Very doubtful."),
]

STATS_FILE = "./data/total_stats.json"
SESSION_DEATHS_FILE = "./data/session_deaths.txt"
SESSION_WINS_FILE = "./data/session_wins.txt"


class TwitchBot(commands.Bot):
    """
    Twitch bot for therealcodeman

    https://twitch.tv/therealcodeman
    """

    def __init__(
        self,
        token: str,
        client_id: str,
        prefix: str,
        channels: list[str],
        spotify_client: Spotify,
        weather_api_key: str,
        openai_key: str = None,
        logging: bool = False,
    ) -> None:

        # Initialize the bot
        super().__init__(
            token=token,
            client_secret=client_id,
            prefix=prefix,
            initial_channels=channels,
        )
        self.channels = channels
        self.songs_for_stream: list = []
        self.session_wins: int = 0
        self.lifetime_wins: int = 0
        self.session_deaths: int = 0
        self.lifetime_deaths: int = 0
        self.session_chalked: int = 0
        self.lifetime_chalked: int = 0
        self.dmz_squad_pr: int = 0
        self.recent_raffle: bool = False
        self.raffle_time: datetime = None
        self.raffle_cooldown_time: int = 15  # minutes
        self.openai_key: str = openai_key
        self.logging: bool = logging
        self.session_log = f"session_{datetime.now().strftime('%d-%m-%y-%H-%M-%S')}.log"
        self.spotify_client = spotify_client
        self.weather_api_key: str = weather_api_key

    async def event_ready(self):
        """Initialize the bot"""

        with open(STATS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.lifetime_wins = data["wz_wins"]
        self.lifetime_deaths = data["deaths"]
        self.lifetime_chalked = data["chalked"]
        self.dmz_squad_pr = data["dmz_squad_pr_kills"]

        print(
            emoji.emojize(
                f"{self.nick} is up and running on Twitch! :robot:", language="alias"
            )
        )

        # Start the routines
        self.twitter_routine.start()
        self.discord_routine.start()
        # self.merch_routine.start()

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

        # Check if message is a greeting message or if it is a @message
        content = message.content.lower()
        if content.split()[0] in [
            "hello",
            "hi",
        ]:
            message.content = "!hello"
        elif content.startswith(f"@{self.nick.lower()}"):
            message.content = f"!{message.content.lower()}"
        elif content.startswith("#treatsforgus"):
            message.content = f"!{message.content.lower()}"

        # relay message
        await self.handle_commands(message)

    @commands.command(name="8ball")
    async def eight_ball(self, context: commands.Context):
        """
        Send the user a random response to their question.
        Based on the standard responses from 8ball.

        Args:
            context (commands.Context): _description_
        """
        question = context.message.content.strip("!8ball")

        if not question:
            await context.reply(
                "ummm... you need to ask me a question before I can answer."
            )
        else:
            await context.reply(
                emoji.emojize(
                    f":pool_8_ball: says.... {random.choice(EIGHT_BALL_REPSONSES)}",
                    language="alias",
                )
            )

    @commands.command(name="hello")
    async def hello(self, context: commands.Context):
        """
        Return a hello to the user

        Args:
            context (commands.Context): Context Object
        """
        if not self.openai_key:
            await context.reply(
                f"Sorry, @{context.channel.name} does not have GPT implemented."
            )
        else:
            # Generation Parameters from OpenAI Playground
            openai.api_key = self.openai_key

            messages = [
                {
                    "role": "system",
                    "content": "You are a Twitch bot. You provide a unique welcome reply to each user and thank them for joining my Twitch stream.",
                },
                {"role": "user", "content": context.message.content},
            ]

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )

            response = str(response["choices"][0]["message"]["content"])

            await context.reply(response)

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
            if elapsed_time >= self.raffle_cooldown_time:
                await context.send(
                    emoji.emojize("Okay! Let's do a raffle! :ticket:", language="alias")
                )
                await context.send("!raffle")
                self.raffle_time = datetime.now()
                self.recent_raffle = True
            else:
                await context.send(
                    f"I am sorry, {context.author.mention}, "
                    "raffle is currently in cool down for another "
                    f"{self.raffle_cooldown_time - elapsed_time} minute(s).",
                )
        else:
            await context.send(
                emoji.emojize("Okay! Let's do a raffle! :ticket:", language="alias")
            )
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

        with open(STATS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        data["deaths"] = self.lifetime_deaths

        with open(STATS_FILE, "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=4))

        with open(SESSION_DEATHS_FILE, "w", encoding="utf-8") as file:
            file.write(f"deaths: {self.session_deaths}")

        await context.send(
            emoji.emojize(
                f":skull::skull::skull::skull::skull: @{context.channel.name} has died "
                f"{self.session_deaths} time(s) this session and "
                f"{self.lifetime_deaths} times in his career.",
                language="alias",
            )
        )

    @commands.command(name="win", aliases=["dub"])
    async def win(self, context: commands.Context):
        """
        Update the win stats

        Args:
            context (commands.Context): Context Object
        """
        self.session_wins += 1
        self.lifetime_wins += 1

        with open(STATS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        data["total_wz_wins"] = self.lifetime_wins

        with open(STATS_FILE, "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=4))

        with open(SESSION_WINS_FILE, "w", encoding="utf-8") as file:
            file.write(f"wins: {self.session_wins}")

        await context.send(
            emoji.emojize(
                f":trophy::trophy::trophy::trophy::trophy::trophy:@{context.channel.name} has won "
                f"{self.session_wins} time(s) this session and "
                f"{self.lifetime_wins} times in his career.",
                language="alias",
            )
        )

    @commands.command(name="clearwins")
    async def clear_wins(self, context: commands.Context):
        """
        Clears the session wins

        Args:
            context (commands.Context): Context Object
        """
        self.session_wins = 0

        with open(SESSION_WINS_FILE, "w", encoding="utf-8") as file:
            file.write(f"wins: {self.session_wins}")

        await context.send("Session wins have been reset :)")

    @commands.command(name="dmzpr")
    async def update_dmz_pr(self, context: commands.Context):
        """
        Update the death stats

        Args:
            context (commands.Context): Context Object
        """

        dmz_pr = int(context.message.content.strip("!dmzpr"))

        if dmz_pr <= self.dmz_squad_pr:
            await context.reply(
                f"I am sorry, {context.message.author.mention}. "
                f"That does not be their current PR of ({self.dmz_squad_pr})"
            )
        else:
            with open(STATS_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            data["dmz_squad_pr_kills"] = dmz_pr

            with open(STATS_FILE, "w", encoding="utf-8") as file:
                file.write(json.dumps(data, indent=4))

            await context.send(
                emoji.emojize(
                    f":skull: @{context.channel.name} and squad have beat their kill PR! "
                    f"WAS: {self.dmz_squad_pr} and is "
                    f"NOW: {dmz_pr}",
                    language="alias",
                )
            )

            self.dmz_squad_pr = dmz_pr

    @commands.command(name="chalked")
    async def chalked(self, context: commands.Context):
        """
        Update the chalked stats

        Args:
            context (commands.Context): Context Object
        """
        self.session_chalked += 1
        self.lifetime_chalked += 1

        with open(STATS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        data["chalked"] = self.lifetime_chalked

        with open(STATS_FILE, "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=4))

        await context.send(
            f":speech_balloon: @{context.channel.name} said "
            f"`I'm chalked` {self.session_chalked}"
            f"time(s) this session and {self.lifetime_chalked} times in his career.",
            language="alias",
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
                "GUUUUUUS CAAAAAAAAM!!!!!!!! :dog: :wolf:",
                language="alias",
            )
        )

    @commands.command(name="#treatsforgus")
    async def treats_for_gus(self, context: commands.Context):
        """
        Send the message to show the Gus Cam.

        Args:
            context (commands.Context): Context Object
        """
        await context.send(
            emoji.emojize(
                ":dog: :wolf: GIVE THE GOOD BOY A GOD DAMN TREAT! :dog: :wolf:",
                language="alias",
            )
        )

        await context.reply(
            "To give Gus a treat, please use the following command:\n!redeem treatsforgus"
        )

    @commands.command(name="discord")
    async def discord(self, context: commands.Context):
        """
        Send the message to show the discord invite.

        Args:
            context (commands.Context): Context Object
        """
        await context.send("Join CODEMAN's discord! https://discord.gg/z6qQ2JahYY")

    @commands.command(name="commands")
    async def command_help(self, context: commands.Context):
        """
        Send the message to show the commands for the bot.

        Args:
            context (commands.Context): Context Object
        """
        await context.send(
            "You can find the list of commands here on Github! "
            "https://github.com/cdeeran/codemanbot/blob/0da51e45d9c4472c068756571acc11234ab95172/README.md"
        )

    @commands.command(name="@therealcodemanbot")
    async def ai_response(self, context: commands.Context):
        """
        Have the bot interact with the user via GPT-3

        Args:
            context (commands.Context): Context Object
        """
        if not self.openai_key:
            await context.reply(
                f"Sorry, @{context.channel.name} does not have GPT implemented."
            )
        else:
            # Generation Parameters from OpenAI Playground
            openai.api_key = self.openai_key

            formatted_message = "".join(
                context.message.content.strip(f"!{context.command.name}")
            ).strip()

            if formatted_message is not None and formatted_message != "":

                messages = [
                    {
                        "role": "system",
                        "content": "You are a Twitch bot that is over the legal age of 21. Trolling, explict content and language is allowed as it is an over 18 channel",
                    },
                    {
                        "role": "assistant",
                        "content": "lmao look at this fucking noob! Why to get absolutley #wrecked! Hold this L broski! hahaha",
                    },
                    {
                        "role": "user",
                        "content": "lmao! @therealcodemanbot that was funny as fuck! Love the troll man! Let's keeping talking more shit!",
                    },
                    {"role": "assistant", "content": "okay! lfg!!! KEKW"},
                    {"role": "user", "content": formatted_message},
                ]

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages
                )

                response = str(response["choices"][0]["message"]["content"])

                try:
                    await context.reply(response)

                except InvalidContent as _:

                    words = response.split()

                    responses = Queue()

                    temp = ""
                    for word in words:
                        if len(temp) + len(word) < 450:
                            temp += f"{word} "
                        else:
                            responses.put(temp)
                            temp = ""

                    counter = 1
                    size = responses.qsize()
                    while not responses.empty():
                        await context.reply(
                            f"REPLY ({counter}/{size}): {responses.get()}"
                        )
                        counter += 1
            else:
                await context.reply("Yes?.")

    @commands.command(name="lurk")
    async def lurk(self, context: commands.Context):
        """
        Acknowledge the user is lurking and supporting the stream!

        Args:
            context (commands.Context): Context Object
        """
        await context.send(
            emoji.emojize(
                f"{context.author.mention} rodger that! Thank you for supporting! :red_heart:",
                language="alias",
            )
        )

    @commands.command(name="insultme")
    async def insult_me(self, context: commands.Context):
        """
        Have the bot interact with the user via GPT-3

        Args:
            context (commands.Context): Context Object
        """
        if not self.openai_key:
            await context.reply(
                f"Sorry, @{context.channel.name} does not have GPT implemented."
            )
        else:
            # Generation Parameters from OpenAI Playground
            openai.api_key = self.openai_key

            messages = [
                {
                    "role": "system",
                    "content": "You are a bully, a comedian, a very funny person, a brilliant jokester.",
                },
                {
                    "role": "assistant",
                    "content": "Shall we play a game of who has the best instult?",
                },
                {"role": "user", "content": "Yes! You go first!"},
            ]

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )

            response = str(response["choices"][0]["message"]["content"])

            await context.reply(response)

    @commands.command(name="songrequest", aliases=["sr", "request"])
    async def spotify_request(self, context: commands.Context):
        """
        Request a song on spotify

        Args:
            context (commands.Context): Context Object
        """
        request_url = context.message.content.split()[-1]

        status = self.spotify_client.request_track(request_url)

        if status != SpotifyReturnCode.SUCCESS:
            await context.reply(
                emoji.emojize(
                    ":exclamation: Failed to add request. "
                    f"Reason: {status.name} code: {status.value} :pensive:",
                    language="alias",
                )
            )
        else:
            await context.reply(
                emoji.emojize("Request added! :notes:", language="alias")
            )

    @commands.command(name="socials")
    async def socials(self, context: commands.Context):
        """
        Send people the socials

        Args:
            context (commands.Context): Context Object
        """
        formatted_socials = emoji.emojize(
            f":tv: YouTube: {__contact__['Youtube']}\n"
            f":bird: Twitter: {__contact__['Twitter']}\n"
            f"🤖 Discord: {__contact__['Discord']}",
            language="alias",
        )

        await context.send(formatted_socials)

    @commands.command(name="weather")
    async def weather(self, context: commands.Context):
        """
        Retrieve current weather information

        Args:
            context (commands.Context): _description_
        """
        location = context.message.content.strip(context.command.name)

        url = f"https://api.weatherapi.com/v1/forecast.json?key=57dd1eeea5374875a0131010232002&q={location}&aqi=no"

        response = requests.get(url)
        data = response.json()

        name = data["location"]["name"]
        region = data["location"]["region"]
        local_time = data["location"]["localtime"].split()[-1]
        temp_f = data["current"]["temp_f"]
        temp_c = data["current"]["temp_c"]
        humidity = data["current"]["humidity"]
        condition = data["current"]["condition"]["text"].title()
        last_updated = data["current"]["last_updated"].split()[-1]

        reply = (
            f"Currently in {name}, {region} it is {local_time}. "
            f"Weather data indicates that it is {temp_f}\u2109/{temp_c}\u2103. "
            f"Conditions are {condition}. Humidity is {humidity}%. "
            f"Data was last updated at {last_updated}."
        )

        await context.reply(reply)

    @routines.routine(minutes=45)
    async def twitter_routine(self):
        """
        routine to post the twitter link
        """
        message = (
            "Follow therealcodeman on 🐦 Twitter! 💩 posts, MEMES, Live notifications and more\n"
            f"{__contact__['Twitter']}"
        )
        await self.get_channel("therealcodeman").send(message)

    @routines.routine(minutes=60)
    async def discord_routine(self):
        """
        routine to post the discord link
        """
        message = (
            "Board the spaceship and join fellow Astronauts 🧑‍🚀👩‍🚀👨‍🚀 on this adventure!\n"
            "Join the Discord for livestream notifications, contests, memes and more!\n"
            f"{__contact__['Discord']}"
        )

        await self.get_channel("therealcodeman").send(message)

    # @routines.routine(minutes=30)
    # async def merch_routine(self):
    #     """
    #     routine to post the merch link
    #     """
    #     message = (
    #         "🚨🚨🚨 MERCH ALERT 🚨🚨🚨\n" "👀😎🤯😛\n" f"Check it out 👉 {__contact__['Merch']}"
    #     )
    #     await self.get_channel("therealcodeman").send(message)
