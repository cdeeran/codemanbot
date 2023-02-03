import twitchio
from twitchio.ext import commands, eventsub
from dotenv import load_dotenv


# Load in the .env file
load_dotenv(".env")

# Constants from .env
TOKEN = os.environ.get("TOKEN")
CLIENT_ID = os.environ.get("CLIENT_ID")
NICKNAME = os.environ.get("NICKNAME")
PREFIX = os.environ.get("PREFIX")
CHANNEL = os.environ.get("CHANNEL")
CHANNEL_URL = os.environ.get("CHANNEL_URL")


esbot = commands.Bot.from_client_credentials(client_id=CLIENT_ID, client_secret=TOKEN)
esclient = eventsub.EventSubClient(
    esbot, webhook_secret="...", callback_route="https://codydeeran.com:443/callback"
)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=TOKEN, prefix="!", initial_channels=[CHANNEL])

    async def __ainit__(self) -> None:
        self.loop.create_task(esclient.listen(port=4000))

        try:
            await esclient.subscribe_channel_follows(broadcaster=CHANNEL)
        except twitchio.HTTPException:
            pass

    async def event_ready(self):
        print("Bot is ready!")


bot = Bot()
bot.loop.run_until_complete(bot.__ainit__())


@esbot.event()
async def event_eventsub_notification_follow(
    payload: eventsub.ChannelFollowData,
) -> None:
    print("Received event!")
    channel = bot.get_channel("channel")
    await channel.send(f"{payload.data.user.name} followed woohoo!")


bot.run()
