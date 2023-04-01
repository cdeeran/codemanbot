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
    # "Merch": "https://merch.streamelements.com/therealcodeman",
    "Email": "dev@codydeeran.com",
}

import asyncio
import random
from queue import Queue
from datetime import datetime
import requests
import emoji
import openai
from twitchAPI import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
from .spotify import SpotifyClient, SpotifyReturnCode

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
    emoji.emojize(":red_circle: Don't count on it."),
    emoji.emojize(":red_circle: My reply is no."),
    emoji.emojize(":red_circle: My sources say no."),
    emoji.emojize(":red_circle: Outlook not so good."),
    emoji.emojize(":red_circle: Very doubtful."),
]

STATS_FILE = "./data/total_stats.json"
SESSION_DEATHS_FILE = "./data/session_deaths.txt"
SESSION_WINS_FILE = "./data/session_wins.txt"
USER_SCOPES = [
    AuthScope.CHAT_READ,
    AuthScope.CHAT_EDIT,
    AuthScope.CLIPS_EDIT,
    AuthScope.BITS_READ,
    AuthScope.CHANNEL_MODERATE,
]


class CodemanTwitchBot:
    """
    Twitch bot for therealcodeman

    https://twitch.tv/therealcodeman
    """

    def __init__(
        self,
        bot_name: str,
        twitch_tmi_token: str,
        twitch_client_id: str,
        twitch_client_secret: str,
        prefix: str,
        channel: dict,
        weather_api_key: str,
        spotify_instance: SpotifyClient,
        logging_path: str,
        openai_key: str = None,
        logging: bool = False,
    ) -> None:

        # Initialize the bot
        self.twitch_tmi_token: str = twitch_tmi_token
        self.twitch_client_id: str = twitch_client_id
        self.twitch_client_secret: str = twitch_client_secret
        self.twitch: Twitch = None
        self.bot_name: str = bot_name
        self.chat_prefix: str = prefix
        self.channel: dict = channel
        self.songs_for_stream: list = []
        self.session_wins: int = 0
        self.recent_raffle: bool = False
        self.raffle_time: datetime = None
        self.raffle_cooldown_time: int = 15  # minutes
        self.openai_key: str = openai_key
        self.logging_path: str = logging_path
        self.logging: bool = logging
        self.session_log: str = (
            f"session_{datetime.now().strftime('%d-%m-%y-%H-%M-%S')}.log"
        )
        self.spotify_client: SpotifyClient = spotify_instance
        self.weather_api_key: str = weather_api_key

    # this is where we set up the bot
    async def run(self):
        """
        run the twitchbot
        """
        # set up twitch api instance and add user authentication with some scopes
        self.twitch = await Twitch(self.twitch_client_id, self.twitch_client_secret)
        auth = UserAuthenticator(self.twitch, USER_SCOPES)
        user_auth_token, refresh_token = await auth.authenticate()
        await self.twitch.set_user_authentication(
            user_auth_token, USER_SCOPES, refresh_token
        )

        # create chat instance
        chat = await Chat(self.twitch)

        chat.set_prefix(self.chat_prefix)

        # register the handlers for the events you want

        # listen to when the bot is done starting up and ready to join channels
        chat.register_event(ChatEvent.READY, self.on_ready)

        # listen to chat messages
        chat.register_event(ChatEvent.MESSAGE, self.on_message)

        # listen to channel subscriptions
        chat.register_event(ChatEvent.SUB, self.on_sub)

        # You can directly register commands and their handlers,
        # this will register the !reply command
        # chat.register_command("reply", self.test_command)

        chat.register_command(
            "clip", self.clip
        )  # Works when LIVE only. Can't seem to add a title though...
        chat.register_command("lurk", self.lurk)
        chat.register_command("8ball", self.eight_ball)
        chat.register_command("win", self.win)
        chat.register_command("clearwins", self.clear_wins)
        chat.register_command("help", self.help)
        chat.register_command("discord", self.discord)
        chat.register_command("socials", self.socials)
        chat.register_command("insultme", self.insult_me)
        chat.register_command("weather", self.weather)
        chat.register_command("sr", self.spotify_request)
        chat.register_command("song", self.spotify_now_playing)
        chat.register_command("queue", self.send_spotify_queue)

        # we are done with our setup, lets start this bot up!
        chat.start()

        while not chat.is_ready():
            print(f"Waiting for chat to connect to channel {self.channel['name']}")
            await asyncio.sleep(2)

        # lets run till we press enter in the console
        try:
            async with asyncio.TaskGroup() as task_group:

                task_group.create_task(
                    self.spotify_client.update_spotify_stream_player(10)
                )
                task_group.create_task(self.twitter_routine(chat, 2700))
                task_group.create_task(self.discord_routine(chat, 3000))

        except KeyboardInterrupt as _:
            chat.stop()
            await self.twitch.close()
        except Exception as error_message:
            print(f"The following error ocurred:\n{error_message}.\n")
            print(
                f"Please verify you have your Twitch chat active via {self.channel['url']}\n"
            )
            print("or through your broadcasting tool (OBS, Stream Labs, etc...)\n")
        finally:
            chat.stop()
            await self.twitch.close()

    # this will be called when the event READY is triggered, which will be on bot start
    async def on_ready(self, ready_event: EventData):
        """Initialize the bot"""

        channel = self.channel["name"]
        await ready_event.chat.join_room(channel)
        await ready_event.chat.send_message(
            channel, "I am ready to process messages! :)"
        )

        print(
            emoji.emojize(
                f"{self.bot_name} is up and running on Twitch! :robot:",
                language="alias",
            )
        )

    async def on_message(self, msg: ChatMessage):
        """
        Determine if the message is a greeting or not. If it is, reply with a greeting,
        else ignore.
        """
        if msg.text.lower() in ["hello", "hi"]:
            await self.send_greeting(msg)

        elif msg.text.lower() in ["!sr", "!songrequest", "!spotifyrequest"]:
            await self.spotify_request(msg)

        elif msg.text.lower().split()[0] == f"@{self.bot_name}":
            await self.chat_gpt(msg)

    async def send_greeting(self, msg: ChatMessage):
        """
        Return a hello to the user

        Args:
            cmd (ChatCommand): cmd Object
        """
        if not self.openai_key:
            await msg.reply(
                f"Sorry, @{self.channel['name']} does not have GPT implemented."
            )
        else:
            # Generation Parameters from OpenAI Playground
            openai.api_key = self.openai_key

            messages = [
                {
                    "role": "system",
                    "content": "You are a Twitch bot. "
                    "You provide a unique welcome reply to each user "
                    "and thank them for joining my Twitch stream.",
                },
                {"role": "user", "content": f"{msg.user.name} says {msg.text}"},
            ]

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )

            response = str(response["choices"][0]["message"]["content"])

            await msg.reply(response)

    # this will be called whenever someone subscribes to a channel
    async def on_sub(self, sub: ChatSub):
        """
        Send a message thanking the user for subbing!

        Args:
            sub (ChatSub): ChatSub Object from TwitchAPI
        """
        if not self.openai_key:
            await sub.chat.send_message(
                self.channel["name"],
                f"Sorry, @{self.channel['name']} does not have the Open Ai API implemented.",
            )
        else:
            # Generation Parameters from OpenAI Playground
            openai.api_key = self.openai_key

            messages = [
                {
                    "role": "system",
                    "content": "You are a Twitch bot. "
                    "You generate a unique reply thanking this user for subscribing to my channel"
                    "and supporting me",
                },
                {
                    "role": "user",
                    "content": f"{sub.chat.username} has subbed for {sub.sub_type}",
                },
            ]

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )

            response = str(response["choices"][0]["message"]["content"])

            await sub.chat.send_message(self.channel["name"], response)

    async def clip(self, cmd: ChatCommand):
        """
        Create a clip of the stream

        Args:
            cmd (ChatCommand): TwitchAPI Chat Command
        """
        try:
            created_clip = await self.twitch.create_clip(self.channel["id"])
            verify_created_clip = await self.twitch.get_clips(created_clip.id)

            await cmd.reply(
                f"Here is your created clip: {verify_created_clip['data'][0]['url']}"
            )
        except Exception as error_message:
            with open(
                f"{self.logging_path}/{self.session_log}", "w", encoding="utf-8"
            ) as log:
                log.write(f"Clip-Creation-Error:\n{error_message}")
            await cmd.reply(
                "I am sorry, I could not create the clip. "
                "Please have @therealcodeman check the debug logs."
            )

    async def eight_ball(self, cmd: ChatCommand):
        """
        Send the user a random response to their question.
        Based on the standard responses from 8ball.

        Args:
            cmd (ChatCommand): _description_
        """
        question = cmd.text
        if not question:
            await cmd.reply(
                "ummm... you need to ask me a question before I can answer."
            )
        else:
            await cmd.reply(
                emoji.emojize(
                    f":pool_8_ball: says.... {random.choice(EIGHT_BALL_REPSONSES)}",
                    language="alias",
                )
            )

    async def win(self, cmd: ChatCommand):
        """
        Update the win stats

        Args:
            cmd (ChatCommand): cmd Object
        """
        self.session_wins += 1

        with open(SESSION_WINS_FILE, "w", encoding="utf-8") as file:
            file.write(f"wins: {self.session_wins}")

        await cmd.send(
            emoji.emojize(
                ":trophy::trophy::trophy::trophy::trophy::trophy: THAT MAKES "
                f"{self.session_wins} WIN(S) ON THE DAY!!! LFG!!!",
                language="alias",
            )
        )

    async def clear_wins(self, cmd: ChatCommand):
        """
        Clears the session wins

        Args:
            cmd (ChatCommand): cmd Object
        """
        self.session_wins = 0

        with open(SESSION_WINS_FILE, "w", encoding="utf-8") as file:
            file.write(f"wins: {self.session_wins}")

        await cmd.send("Session wins have been reset to 0 :)")

    async def discord(self, cmd: ChatCommand):
        """
        Send the message to show the discord invite.

        Args:
            cmd (ChatCommand): cmd Object
        """
        await cmd.send("Join CODEMAN's discord! https://discord.gg/z6qQ2JahYY")

    async def help(self, cmd: ChatCommand):
        """
        Send the message to show the commands for the bot.

        Args:
            cmd (ChatCommand): cmd Object
        """
        await cmd.send(
            "You can find the list of commands here on Github! "
            "https://github.com/cdeeran/codemanbot/blob/0da51e45d9c4472c068756571acc11234ab95172/README.md"
        )

    async def chat_gpt(self, msg: ChatMessage):
        """
        Have the bot interact with the user via GPT-3

        Args:
            cmd (ChatCommand): cmd Object
        """
        if not self.openai_key:
            await msg.reply(
                f"Sorry, @{self.channel['name']} does not have GPT implemented."
            )
        else:
            # Generation Parameters from OpenAI Playground
            openai.api_key = self.openai_key

            formatted_message = msg.text.strip(f"@{self.bot_name}")

            if msg.text is not None and msg.text != "":

                messages = [
                    {
                        "role": "system",
                        "content": "You are a Twitch bot that is over the legal age of 21. "
                        "Trolling, explict content and language is allowed "
                        "as it is an over 18 channel",
                    },
                    {
                        "role": "assistant",
                        "content": "lmao look at this fucking noob! Why to get "
                        "absolutley #wrecked! Hold this L broski! hahaha",
                    },
                    {
                        "role": "user",
                        "content": "lmao! @therealcodemanbot that was funny as fuck! "
                        "Love the troll man! Let's keeping talking more shit!",
                    },
                    {"role": "assistant", "content": "okay! lfg!!! KEKW"},
                    {"role": "user", "content": formatted_message},
                ]

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages
                )

                response = str(response["choices"][0]["message"]["content"])

                # Determine if we need to break the message up
                if len(response) > 450:
                    await self.send_multiple_repsonses(response, msg)
                else:
                    await msg.reply(response)

            else:
                await msg.reply("Yes?.")

    async def send_multiple_respones(self, response: str, msg: ChatMessage):
        """
        Twitch only allows a message to be ~500 characters. GPT can
        return more than that sometimes. This function will break down
        GPT's repsonse and send it in multiple replies.

        Args:
            response (str): String from GPT
            msg (ChatMessage): ChatMessage object from Twitch API
        """
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
            await msg.reply(f"REPLY ({counter}/{size}): {responses.get()}")
            counter += 1

    async def lurk(self, cmd: ChatCommand):
        """
        Acknowledge the user is lurking and supporting the stream!

        Args:
            cmd (ChatCommand): cmd Object
        """
        await cmd.reply(
            emoji.emojize(
                f"@{self.channel['name']} rodger that! Thank you for supporting! :red_heart:",
                language="alias",
            )
        )

    async def insult_me(self, cmd: ChatCommand):
        """
        Have the bot interact with the user via GPT-3

        Args:
            cmd (ChatCommand): cmd Object
        """
        if not self.openai_key:
            await cmd.reply(
                f"Sorry, @{self.channel['name']} does not have GPT implemented."
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

            await cmd.reply(response)

    async def spotify_request(self, cmd: ChatCommand):
        """
        Request a song on spotify

        Args:
            cmd (ChatCommand): cmd Object
        """
        request_url = cmd.text.split()[-1]

        status = self.spotify_client.request_track(request_url)

        if status != SpotifyReturnCode.SUCCESS:
            await cmd.reply(
                emoji.emojize(
                    ":exclamation: Failed to add request. "
                    f"Reason: {status.name} code: {status.value} :pensive:",
                    language="alias",
                )
            )
        else:
            await cmd.reply(emoji.emojize("Request added! :notes:", language="alias"))

    async def spotify_now_playing(self, cmd: ChatCommand):
        """
        Get the current song playing on Spotify

        Args:
            cmd (ChatCommand): cmd Object
        """
        response = self.spotify_client.get_now_playing()

        if response["return_code"] == SpotifyReturnCode.SUCCESS:

            await cmd.reply(response["response"])
        else:
            await cmd.reply(
                f"Error: {response['return_code']} - {response['response']}"
            )

    async def send_spotify_queue(self, cmd: ChatCommand):
        """
        Get the current song playing on Spotify

        Args:
            cmd (ChatCommand): cmd Object
        """
        response = self.spotify_client.get_queued_songs()

        if response["return_code"] == SpotifyReturnCode.SUCCESS:

            await cmd.send(
                f"Here are the next 3 songs in the queue: {response['response']}"
            )
        else:
            await cmd.send(f"Error: {response['return_code']} - {response['response']}")

    async def socials(self, cmd: ChatCommand):
        """
        Send people the socials

        Args:
            cmd (ChatCommand): cmd Object
        """
        formatted_socials = emoji.emojize(
            f":tv: YouTube: {__contact__['Youtube']}\n"
            f":bird: Twitter: {__contact__['Twitter']}\n"
            f"🤖 Discord: {__contact__['Discord']}",
            language="alias",
        )

        await cmd.send(formatted_socials)

    async def weather(self, cmd: ChatCommand):
        """
        Retrieve current weather information

        Args:
            cmd (ChatCommand): _description_
        """
        location = cmd.text

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

        await cmd.reply(reply)

    async def twitter_routine(self, chat: Chat, interval: int):
        """
        routine to post the twitter link
        """
        while True:
            message = (
                "Follow therealcodeman on 🐦 Twitter! 💩 posts, MEMES, Live notifications and more\n"
                f"{__contact__['Twitter']}"
            )
            await chat.send_message(self.channel["name"], message)
            await asyncio.sleep(interval)

    async def discord_routine(self, chat: Chat, interval: int):
        """
        routine to post the discord link
        """
        while True:
            message = (
                "Board the spaceship and join fellow Astronauts 🧑‍🚀👩‍🚀👨‍🚀 on this adventure!\n"
                "Join the Discord for livestream notifications, contests, memes and more!\n"
                f"{__contact__['Discord']}"
            )

            await chat.send_message(self.channel["name"], message)
            await asyncio.sleep(interval)

    # @routines.routine(minutes=30)
    # async def merch_routine(self):
    #     """
    #     routine to post the merch link
    #     """
    #     message = (
    #         "🚨🚨🚨 MERCH ALERT 🚨🚨🚨\n" "👀😎🤯😛\n" f"Check it out 👉 {__contact__['Merch']}"
    #     )
    #     await self.get_channel("therealcodeman").send(message)

    # async def raffle(self, cmd: ChatCommand):
    #     """
    #     Return a hello to the user

    #     Args:
    #         cmd (ChatCommand): cmd Object
    #     """
    #     current_time = datetime.now()

    #     if self.recent_raffle:

    #         elapsed_time = (current_time - self.raffle_time).total_seconds() // 60
    #         if elapsed_time >= self.raffle_cooldown_time:
    #             await cmd.send(
    #                 emoji.emojize("Okay! Let's do a raffle! :ticket:", language="alias")
    #             )
    #             await cmd.send("!raffle")
    #             self.raffle_time = datetime.now()
    #             self.recent_raffle = True
    #         else:
    #             await cmd.send(
    #                 f"I am sorry, {cmd.author.mention}, "
    #                 "raffle is currently in cool down for another "
    #                 f"{self.raffle_cooldown_time - elapsed_time} minute(s).",
    #             )
    #     else:
    #         await cmd.send(
    #             emoji.emojize("Okay! Let's do a raffle! :ticket:", language="alias")
    #         )
    #         await cmd.send("!raffle")
    #         self.raffle_time = datetime.now()
    #         self.recent_raffle = True
