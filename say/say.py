# Say by retke, aka El Laggron

import re
from logging import getLogger
from typing import Optional

import discord
from bot import ModmailBot
from core import checks
from core.models import PermissionLevel
from discord.ext import commands

logger = getLogger(__name__)

ROLE_MENTION_REGEX = re.compile(r"<@&(?P<id>[0-9]{17,19})>")


class Say(commands.Cog):
    """
    Speak as if you were the bot

    Documentation: http://laggron.red/say.html
    """

    def __init__(self, bot: ModmailBot):
        self.bot = bot
        self.interaction = []

    __author__ = ["retke (El Laggron)", "raidensakura"]
    __version__ = "1.0.0"

    async def say(
        self,
        ctx: commands.Context,
        channel: Optional[discord.TextChannel],
        text: str,
        mentions: discord.AllowedMentions = None,
        delete: int = None,
    ):
        if not channel:
            channel = ctx.channel
        if not text:
            await ctx.send_help(ctx.command)
            return

        author = ctx.author
        guild = channel.guild

        # checking perms
        if guild and not channel.permissions_for(guild.me).send_messages:
            if channel != ctx.channel:
                await ctx.send(
                    ("I am not allowed to send messages in ") + channel.mention,
                    delete_after=2,
                )
            else:
                await author.send(("I am not allowed to send messages in ") + channel.mention)
            return

        try:
            await channel.send(text, allowed_mentions=mentions, delete_after=delete)
        except discord.errors.HTTPException:
            try:
                await ctx.send("An error occured when sending the message.")
            except discord.errors.HTTPException:
                pass
            logger.error("Failed to send message.", exc_info=True)

    @commands.command(name="say")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def _say(self, ctx: commands.Context, channel: Optional[discord.TextChannel], *, text: str = ""):
        """
        Make the bot say what you want in the desired channel.

        If no channel is specified, the message will be send in the current channel.

        Example usage :
        - `!say #general hello there`
        """

        await self.say(ctx, channel, text)

    @commands.command(name="sayad")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def _sayautodelete(
        self,
        ctx: commands.Context,
        channel: Optional[discord.TextChannel],
        delete_delay: int,
        *,
        text: str = "",
    ):
        """
        Same as say command, except it deletes the said message after a set number of seconds.
        """

        await self.say(ctx, channel, text, delete=delete_delay)

    @commands.command(name="sayd", aliases=["sd"])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def _saydelete(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel], *, text: str = ""
    ):
        """
        Same as say command, except it deletes your message.

        If the message wasn't removed, then I don't have enough permissions.
        """

        author = ctx.author

        try:
            await ctx.message.delete()
        except discord.errors.Forbidden:
            try:
                await ctx.send(("Not enough permissions to delete messages."), delete_after=2)
            except discord.errors.Forbidden:
                await author.send(("Not enough permissions to delete messages."), delete_after=15)

        await self.say(ctx, channel, text)

    @commands.command(name="saym", aliases=["sm"])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def _saymention(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel], *, text: str = ""
    ):
        """
        Same as say command, except role and mass mentions are enabled.
        """
        message = ctx.message
        channel = channel or ctx.channel
        guild = channel.guild

        role_mentions = list(
            filter(
                None,
                (ctx.guild.get_role(int(x)) for x in ROLE_MENTION_REGEX.findall(message.content)),
            )
        )
        mention_everyone = "@everyone" in message.content or "@here" in message.content
        if not role_mentions and not mention_everyone:
            # no mentions, nothing to check
            return await self.say(ctx, channel, text)
        non_mentionable_roles = [x for x in role_mentions if x.mentionable is False]

        if not channel.permissions_for(guild.me).mention_everyone:
            if non_mentionable_roles:
                await ctx.send(
                    (
                        "I can't mention the following roles: {roles}\nTurn on "
                        "mentions or grant me the correct permissions.\n"
                    ).format(roles=", ".join([x.name for x in non_mentionable_roles]))
                )
                return
            if mention_everyone:
                await ctx.send(("I don't have the permission to mention everyone."))
                return
        if not channel.permissions_for(ctx.author).mention_everyone:
            if non_mentionable_roles:
                await ctx.send(
                    (
                        "You're not allowed to mention the following roles: {roles}\nTurn on "
                        "mentions for that role or have the correct permissions.\n"
                    ).format(roles=", ".join([x.name for x in non_mentionable_roles]))
                )
                return
            if mention_everyone:
                await ctx.send(("You don't have the permission yourself to do mass mentions."))
                return
        await self.say(ctx, channel, text, mentions=discord.AllowedMentions(everyone=True, roles=True))

    @commands.command(hidden=True)
    @checks.has_permissions(PermissionLevel.OWNER)
    async def sayinfo(self, ctx):
        """
        Get informations about the cog.
        """
        e = discord.Embed(
            color=ctx.bot.main_color,
            title="Laggron's Dumb Cogs - say",
            description="Originally made for Red Discord bot, ported to Modmail by raidensakura.",
        )
        e.add_field(
            name="Original Repository", value="https://github.com/retke/Laggrons-Dumb-Cogs/", inline=False
        )
        e.add_field(
            name="Plugin Repository", value="https://github.com/raidensakura/modmail-plugins", inline=False
        )
        e.add_field(name="Version", value=f"{self.__version__}")
        e.add_field(name="Author", value=f"{', '.join(self.__author__)}")
        await ctx.send(embed=e)

    async def cog_unload(self):
        logger.debug("Unloading cog...")
        for user in self.interaction:
            await self.stop_interaction(user)


async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(Say(bot))
