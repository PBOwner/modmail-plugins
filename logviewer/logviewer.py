from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from core import checks
from core.models import PermissionLevel, getLogger
from core.utils import strtobool
from discord.ext import commands
from discord.utils import MISSING

from .core.servers import LogviewerServer

if TYPE_CHECKING:
    from bot import ModmailBot

info_json = Path(__file__).parent.resolve() / "info.json"
with open(info_json, encoding="utf-8") as f:
    __plugin_info__ = json.loads(f.read())

__plugin_name__ = __plugin_info__["name"]
__version__ = __plugin_info__["version"]
__description__ = "\n".join(__plugin_info__["description"]).format(__plugin_info__["wiki"], __version__)

logger = getLogger(__name__)


class Logviewer(commands.Cog, name=__plugin_name__):
    __doc__ = __description__

    def __init__(self, bot: ModmailBot):
        self.bot: ModmailBot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        self.config = None
        self.default_config = {
            "log_url": "http://localhost:8000",
            "oauth2_client_id": None,
            "oauth2_client_secret": None,
            "oauth2_redirect_uri": None,
            "host": "0.0.0.0",
            "port": 8000,
            "log_url_prefix": "/logs",
            "pagination": 25,
            "ssl_cert_path": None,
            "ssl_key_path": None,
            "encryption_key": "A sophisticated key",
        }
        self.server: LogviewerServer = MISSING

    async def cog_load(self) -> None:
        self.config = await self.db.find_one({"_id": "logviewer"})
        if not self.config:
            self.config = self.default_config
        self.config["oauth2_client_id"] = self.bot.user.id
        log_url = os.getenv("LOG_URL", self.config["log_url"])
        if log_url:
            self.config["oauth2_redirect_uri"] = (
                f"{log_url}callback" if log_url.endswith("/") else f"{log_url}/callback"
            )
        await self.update_config()
        if strtobool(os.environ.get("LOGVIEWER_AUTOSTART", True)):
            self.server = LogviewerServer(self.bot, config=self.config)
            await self.server.start()

    async def update_config(self):
        await self.db.find_one_and_update(
            {"_id": "logviewer"},
            {"$set": self.config},
            upsert=True,
        )

    async def cog_unload(self) -> None:
        await self._stop_server()

    async def _stop_server(self) -> None:
        if self.server:
            await self.server.stop()
            self.server = MISSING

    @commands.group(name="logviewer", invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.OWNER)
    async def logviewer(self, ctx: commands.Context):
        """
        Log viewer manager.
        """
        await ctx.send_help(ctx.command)

    @logviewer.group(name="config", invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.OWNER)
    async def logviewer_config(self, ctx: commands.Context):
        """
        Command group for configuring logviewer variables.
        """
        await ctx.send_help(ctx.command)

    @logviewer_config.command(name="secret")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def set_secret(self, ctx: commands.Context, *, secret: str):
        """
        Set OAuth2 client secret for logviewer.

        Note: `OAUTH2_CLIENT_SECRET` environment variable will always override this settings.
        """
        self.config["oauth2_client_secret"] = secret
        await self.update_config()
        await ctx.message.delete()
        await ctx.send("OAuth2 client secret set.")

    @logviewer_config.command(name="certpath")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def set_certpath(self, ctx: commands.Context, *, path: str):
        """
        Set path pointing to the certificate file for SSL. The file must exist on the system/container. Must be set alongside `[prefix]logviewer config keypath`
        for SSL to be enabled. Webserver must be restarted for this change to take effect.

        Note: `SSL_CERT_PATH` environment variable will always override this settings.
        """
        self.config["ssl_cert_path"] = path
        await self.update_config()
        await ctx.message.delete()
        await ctx.send("SSL certificate path set.")

    @logviewer_config.command(name="keypath")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def set_keypath(self, ctx: commands.Context, *, path: str):
        """
        Set path pointing to the certificate key file for SSL. The file must exist on the system/container. Must be set alongside `[prefix]logviewer config certpath`
        for SSL to be enabled. Webserver must be restarted for this change to take effect.

        Note: `SSL_KEY_PATH` environment variable will always override this settings.
        """
        self.config["ssl_key_path"] = path
        await self.update_config()
        await ctx.message.delete()
        await ctx.send("SSL certificate key path set.")

    @logviewer_config.command(name="encryption_key", aliases=["session_key"])
    @checks.has_permissions(PermissionLevel.OWNER)
    async def set_encryption_key(self, ctx: commands.Context, *, key: str):
        """
        Set encryption key for the Logviewer session. This is used to encrypt and decrypt user session cookies. Webserver must be restarted for this change to take effect.
        """
        self.config["encryption_key"] = key
        await self.update_config()
        await ctx.message.delete()
        await ctx.send("Logviewer encryption key set.")

    @logviewer_config.command(name="port")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def set_port(self, ctx: commands.Context, port: int):
        """
        Set the webserer port for Logviewer to listen on. Webserver must be restarted for this change to take effect.
        """
        self.config["port"] = port
        await self.update_config()
        await ctx.send("Logviewer port set.")

    @logviewer_config.group(name="remove", aliases=["reset", "delete"])
    @checks.has_permissions(PermissionLevel.OWNER)
    async def remove_config(self, ctx: commands.Context):
        """
        Command group for removing logviewer configuration.
        """

    @remove_config.command(name="secret")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def remove_secret(self, ctx: commands.Context):
        """
        Remove OAuth2 client secret.
        """
        self.config["oauth2_client_secret"] = None
        await self.update_config()
        await ctx.send("OAuth2 client secret removed.")

    @remove_config.command(name="certpath")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def remove_certpath(self, ctx: commands.Context):
        """
        Remove SSL certificate path. Webserver must be restarted for this change to take effect.
        """
        self.config["ssl_cert_path"] = None
        await self.update_config()
        await ctx.send("SSL certificate path removed.")

    @remove_config.command(name="keypath")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def remove_keypath(self, ctx: commands.Context):
        """
        Remove SSl certificate key path. Webserver must be restarted for this change to take effect.
        """
        self.config["ssl_key_path"] = None
        await self.update_config()
        await ctx.send("SSL certificate key path removed.")

    @remove_config.command(name="encryption_key", aliases=["session_key"])
    @checks.has_permissions(PermissionLevel.OWNER)
    async def remove_encryption_key(self, ctx: commands.Context):
        """
        Remove custom encryption key for the Logviewer session. Webserver must be restarted for this change to take effect.
        """
        self.config["encryption_key"] = None
        await self.update_config()
        await ctx.send("Logviewer encryption key removed.")

    @logviewer.command(name="start")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def lv_start(self, ctx: commands.Context):
        """
        Starts the log viewer server.
        """
        if self.server:
            raise commands.BadArgument("Logviewer server is already running.")

        self.server = LogviewerServer(self.bot, config=self.config)
        await self.server.start()
        embed = discord.Embed(
            title="Start",
            color=self.bot.main_color,
            description="Logviewer server is now running.",
        )
        await ctx.send(embed=embed)

    @logviewer.command(name="stop")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def lv_stop(self, ctx: commands.Context):
        """
        Stops the log viewer.
        """
        if not self.server:
            raise commands.BadArgument("Logviewer server is not running.")
        await self._stop_server()
        embed = discord.Embed(
            title="Stop",
            color=self.bot.main_color,
            description="Logviewer server is now stopped.",
        )
        await ctx.send(embed=embed)

    @logviewer.command(name="info")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def lv_info(self, ctx: commands.Context):
        """
        Shows information of the logviewer.
        """
        if not self.server:
            raise commands.BadArgument("Logviewer server is not running.")

        embed = discord.Embed(
            title="__Homepage__",
            color=self.bot.main_color,
            url=self.config["log_url"],
        )
        embed.set_author(
            name="Logviewer",
            icon_url=self.bot.user.display_avatar.url,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        main_deps = self.server.info()
        embed.description = f"Serving over `{'HTTPS' if self.server.is_https else 'HTTP'}` on port `{self.server.config.port}`.\n"
        embed.add_field(name="Dependencies", value=f"```py\n{main_deps}\n```")

        embed.set_footer(text=f"Version: v{__version__}")

        await ctx.send(embed=embed)


async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(Logviewer(bot))
