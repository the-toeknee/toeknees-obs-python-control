"""An example of connecting to a conduit and subscribing to EventSub when a User Authorizes the application.

This bot can be restarted as many times without needing to subscribe or worry about tokens:
- Tokens are stored in '.tio.tokens.json' by default
- Subscriptions last 72 hours after the bot is disconnected and refresh when the bot starts.

Consider reading through the documentation for AutoBot for more in depth explanations.
https://twitchio.dev/en/latest/getting-started/quickstart.html
"""

import logging
import asyncio
import aiofiles
import logging
from typing import TYPE_CHECKING
from datetime import datetime
from os import getenv
import pygtail
import asqlite

import twitchio
from twitchio import eventsub
from twitchio.ext import commands


if TYPE_CHECKING:
    import sqlite3


LOGGER: logging.Logger = logging.getLogger("Bot")

# Consider using a .env or another form of Configuration file!
CLIENT_ID: str = getenv(
    "TWITCH_BOT_CLIENT_ID"
)  # The CLIENT ID from the Twitch Dev Console
CLIENT_SECRET: str = getenv(
    "TWITCH_BOT_CLIENT_SECRET"
)  # The CLIENT SECRET from the Twitch Dev Console
BOT_ID = "1351292067"  # The Account ID of the bot user...
OWNER_ID = "27329615"  # Your personal User ID..

START_DATE = datetime.now().strftime("%Y-%m-%d")
CHAT_LOG_DIR = "ChatLog"
CHAT_FILE_PREFIX = "chat_log"
CHAT_FILE = f"{CHAT_LOG_DIR}/{CHAT_FILE_PREFIX}_{START_DATE}.txt"  # Date of chat timestamped with when da bot started.
REDEEM_FILE = f"{CHAT_LOG_DIR}/redeem_{START_DATE}.txt"


# Click open only for personal twitch account????????
# http://localhost:4343/oauth?scopes=user:read:chat%20user:write:chat%20channel:read:redemptions%20channel:manage:redemptions%20user:bot&force_verify=true
class Bot(commands.AutoBot):
    def __init__(
        self, *, token_database: asqlite.Pool, subs: list[eventsub.SubscriptionPayload]
    ) -> None:
        self.token_database = token_database

        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="!",
            subscriptions=subs,
            force_subscribe=True,
        )

    async def setup_hook(self) -> None:
        # Add our component which contains our commands...
        await self.add_component(MyComponent(self))

    async def event_oauth_authorized(
        self, payload: twitchio.authentication.UserTokenPayload
    ) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # We usually don't want subscribe to events on the bots channel...
            return

        # A list of subscriptions we would like to make to the newly authorized channel...
        # https://twitchio.dev/en/latest/references/events/events.html#table-reference
        subs: list[eventsub.SubscriptionPayload] = [
            # Chat Messages
            eventsub.ChatMessageSubscription(
                broadcaster_user_id=payload.user_id, user_id=self.bot_id
            ),
            # Custom Channel Point Redemptions
            eventsub.ChannelPointsRedeemAddSubscription(
                broadcaster_user_id=payload.user_id
            ),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            LOGGER.warning(
                "Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id
            )
        else:
            LOGGER.info(
                "Successfully subscribed to: %r, for user: %s",
                resp.data,
                payload.user_id,
            )

    async def add_token(
        self, token: str, refresh: str
    ) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(
            token, refresh
        )

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Added token to the database for user: %s", resp.user_id)
        LOGGER.info(f"User {resp.user_id} has scopes:{resp.scopes}")
        return resp

    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.bot_id)


class MyComponent(commands.Component):
    # An example of a Component with some simple commands and listeners
    # You can use Components within modules for a more organized codebase and hot-reloading.

    def __init__(self, bot: Bot) -> None:
        # Passing args is not required...
        # We pass bot here as an example...
        self.bot = bot
        self.chat_log_file = CHAT_FILE
        self.redeem_file = REDEEM_FILE
        try:
            with open(self.chat_log_file, "x") as f:
                f.write("")
        except FileExistsError:
            LOGGER.warning("File %s already exists!", self.chat_log_file)

        try:
            with open(self.redeem_file, "x") as f:
                f.write("")
        except FileExistsError:
            LOGGER.warning("File %s already exists!", self.redeem_file)

    # An example of listening to an event
    # We use a listener in our Component to display the messages received.
    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        chat_message = f"{payload.chatter.name}: {payload.text}"
        LOGGER.info(chat_message)
        async with aiofiles.open(self.chat_log_file, mode="a") as f:
            await f.write(chat_message + "\n")

    #  ChannelPointsRedeemAddSubscription
    @commands.Component.listener()
    async def event_custom_redemption_add(
        self, payload: twitchio.ChannelPointsRedemptionAdd
    ) -> None:
        reward_title = payload.reward.title
        user = payload.user.name
        user_input = payload.user_input
        redeem_message = f"{reward_title};{user};{user_input}\n"
        LOGGER.info(redeem_message)
        async with aiofiles.open(self.redeem_file, mode="a") as f:
            await f.write(redeem_message)


async def setup_database(
    db: asqlite.Pool,
) -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:
    # Create our token table, if it doesn't exist..
    # You should add the created files to .gitignore or potentially store them somewhere safer
    # This is just for example purposes...

    query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
    async with db.acquire() as connection:
        await connection.execute(query)

        # Fetch any existing tokens...
        rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        tokens: list[tuple[str, str]] = []
        subs: list[eventsub.SubscriptionPayload] = []

        for row in rows:
            tokens.append((row["token"], row["refresh"]))

            if row["user_id"] == BOT_ID:
                continue

            LOGGER.info("User Id to subscribe to messages: %s", str(row["user_id"]))

            subs.extend(
                [
                    eventsub.ChatMessageSubscription(
                        broadcaster_user_id=row["user_id"], user_id=BOT_ID
                    ),
                    # Custom Channel Point Redemptions
                    eventsub.ChannelPointsRedeemAddSubscription(
                        broadcaster_user_id=row["user_id"]
                    ),
                ]
            )

    return tokens, subs


# Our main entry point for our Bot
# Best to setup_logging here, before anything starts
def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb:
            tokens, subs = await setup_database(tdb)

            async with Bot(token_database=tdb, subs=subs) as bot:
                for pair in tokens:
                    await bot.add_token(*pair)

                # await bot.start(load_tokens=False)
                await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt")


if __name__ == "__main__":
    main()
