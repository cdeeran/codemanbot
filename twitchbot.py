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
    "Email": "dev@codydeeran.com",
}

import json
from datetime import datetime
import random
import emoji
import openai
from twitchio.ext import commands
from twitchio.message import Message

# from dotenv import load_dotenv


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
        self.pocus_troll: bool = False
        self.session_log = f"session_{datetime.now().strftime('%d-%m-%y-%H-%M-%S')}.log"

    async def event_ready(self):
        """Initialize the bot"""

        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        self.lifetime_deaths = data["deaths"]
        self.lifetime_chalked = data["chalked"]
        self.dmz_squad_pr = data["dmz_squad_pr_kills"]

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

        if not self.pocus_troll and "pocus_jet" in message.author.name.lower():
            message.content = "!troll"
            self.pocus_troll = True

        if self.logging:
            with open(f"./.logs/{self.session_log}", "a+", encoding="utf-8") as log:
                log.write(f"{message.author.name}: {message.content}\n\n")

        # Check if message is a greeting message or if it is a @message
        content = message.content.lower()
        if content.split()[0] in [
            "hello",
            "hi",
            "sup",
            "what's up",
            "whats up",
            "what up",
            "wat up",
            "yo",
        ]:
            message.content = f"!{message.content.lower()}"
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
                    f":pool_8_ball: says.... {random.choice(EIGHT_BALL_REPSONSES)}"
                )
            )

    @commands.command(name="troll")
    async def troll(self, context: commands.Context):
        """
        Troll the Pocus_Jet user

        Args:
            context (commands.Context): Context Object
        """
        await context.reply("HELLO MUTHAFUCKA! HEY, HI, HOW YA DERRIN?!")

    @commands.command(name="hello")
    async def hello(self, context: commands.Context):
        """
        Return a hello to the user

        Args:
            context (commands.Context): Context Object
        """
        await context.reply(f"Hello {context.author.mention}!")

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
                await context.send(emoji.emojize("Okay! Let's do a raffle! :ticket:"))
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
            await context.send(emoji.emojize("Okay! Let's do a raffle! :ticket:"))
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

        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        data["deaths"] = self.lifetime_deaths

        with open("data.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=4))

        await context.send(
            emoji.emojize(
                f":skull: @{context.channel.name} has died "
                f"{self.session_deaths} time(s) this session and "
                f"{self.lifetime_deaths} times in his career.",
            )
        )

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
            with open("data.json", "r", encoding="utf-8") as file:
                data = json.load(file)

            data["dmz_squad_pr_kills"] = dmz_pr

            with open("data.json", "w", encoding="utf-8") as file:
                file.write(json.dumps(data, indent=4))

            await context.send(
                emoji.emojize(
                    f":skull: @{context.channel.name} and squad have beat their kill PR! "
                    f"WAS: {self.dmz_squad_pr} and is "
                    f"NOW: {dmz_pr}",
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

        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        data["chalked"] = self.lifetime_chalked

        with open("data.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=4))

        await context.send(
            f":speech_balloon: @{context.channel.name} said "
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

    @commands.command(name="#treatsforgus")
    async def treats_for_gus(self, context: commands.Context):
        """
        Send the message to show the Gus Cam.

        Args:
            context (commands.Context): Context Object
        """
        await context.send(
            emoji.emojize(
                ":dog: :wolf: GIVE THE GOOD BOY A GOD DAMN TREAT! :dog: :wolf:"
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

                response = openai.Completion.create(
                    model="text-ada-001",
                    prompt=f"{formatted_message}"
                    if formatted_message[-1] == "?"
                    else f"{formatted_message}?",
                    max_tokens=35,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )

                response = str(response["choices"][0]["text"])

            else:
                response = "Yes?..."

            await context.reply(response)

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

            response = openai.Completion.create(
                model="text-ada-001",
                prompt="write an insult about me",
                max_tokens=35,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )

            response = str(response["choices"][0]["text"])

            await context.reply(response)

    # @commands.command(name="gamble", aliases=["roulette"])
    # async def gamble_points(self, context: commands.Context):

    #     message = context.message.content.split()

    #     points = message[1]

    #     random.seed(version=2)

    #     number = random.randint(1, 100)

    #     win = True if number > 50 else False

    #     if win:
    #         reply_message = emoji.emojize(
    #             f":slot_machine: :game_dice: WOOOHOOO!!! {context.author.mention} "
    #             + f"JUST WON {points}! :slot_machine: :game_dice:"
    #             + "FeelsBadGuy FeelsBadGuy"
    #         )
    #         await context.reply(reply_message)
    #         await context.reply(f"!addpoints {context.author.name} {points}")
    #     else:
    #         reply_message = emoji.emojize(
    #             f":slot_machine: :game_dice: WOOOHOOO!!! {context.author.mention} "
    #             + f"JUST WON {points}! :slot_machine: :game_dice:"
    #             + "FeelsBadGuy FeelsBadGuy"
    #         )
    #         await context.reply(reply_message)
    #         await context.reply(f"!addpoints {context.author.name} {points}")
