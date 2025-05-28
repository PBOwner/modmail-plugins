import re
from logging import getLogger

import discord
from bot import ModmailBot
from core.thread import Thread
from discord.ext import commands

logger = getLogger(__name__)

ROLE_MENTION_REGEX = re.compile(r"<@&(?P<id>[0-9]{17,19})>")


class VideoPreview(commands.Cog):
    """
    Embed a video sent through the Modmail thread to show its preview.
    """

    def __init__(self, bot: ModmailBot):
        self.bot = bot
        self.interaction = []

    __author__ = ["raidensakura"]
    __version__ = "1.0.0"

    async def cog_unload(self):
        logger.debug("Unloading cog...")
        for user in self.interaction:
            await self.stop_interaction(user)

    @commands.Cog.listener()
    async def on_thread_reply(
        self, thread: Thread, from_mod: bool, message: discord.Message, anon: bool, plain: bool
    ) -> None:
        if not message.attachments:
            return

        msg = ""
        for i, attachment in enumerate(message.attachments):
            if attachment.filename.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
                msg += f"Video Preview ({i+1})\n{attachment.url}\n"

        if from_mod:
            await thread.recipient.send(msg)
        else:
            await thread.channel.send(msg)


async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(VideoPreview(bot))
