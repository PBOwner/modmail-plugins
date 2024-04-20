from __future__ import annotations

from datetime import datetime
from time import time
from typing import TYPE_CHECKING, List, Optional, Union
from urllib.parse import parse_qs, urlparse

import dateutil.parser
from bot import ModmailBot
from core.models import getLogger
from discord import DMChannel
from natural.date import duration

from .formatter import format_content_html

logger = getLogger(__name__)

if TYPE_CHECKING:
    from .types_ext import (
        AttachmentPayload,
        AuthorPayload,
        LogEntryPayload,
        MessagePayload,
    )

cache = {"users": {}, "dm_channels": {}, "messages": {}}


class LogEntry:
    def __init__(self, data: LogEntryPayload, bot: ModmailBot):
        self.key: str = data["key"]
        self.open: bool = data["open"]

        self.created_at: datetime = dateutil.parser.parse(data["created_at"])
        if self.created_at.tzinfo is not None:
            self.created_at = self.created_at.replace(tzinfo=None)

        self.human_created_at: str = duration(self.created_at, now=datetime.utcnow())
        self.closed_at: Optional[datetime] = (
            dateutil.parser.parse(data["closed_at"]) if not self.open else None
        )
        if self.closed_at is not None and self.closed_at.tzinfo is not None:
            self.closed_at = self.closed_at.replace(tzinfo=None)

        self.channel_id: int = int(data["channel_id"])
        self.guild_id: int = int(data["guild_id"])
        self.creator: Author = Author(data["creator"])
        self.recipient: Author = Author(data["recipient"])
        self.closer: Author = Author(data["closer"]) if not self.open else None
        self.close_message: str = format_content_html(data.get("close_message") or "")
        self.messages: List[Message] = [Message(m, bot) for m in data["messages"]]
        self.internal_messages: List[Message] = [m for m in self.messages if m.type == "internal"]
        self.thread_messages: List[Message] = [
            m for m in self.messages if m.type not in ("internal", "system")
        ]

    @property
    def system_avatar_url(self) -> str:
        return "/static/img/avatar_self.png"

    @property
    def human_closed_at(self) -> str:
        return duration(self.closed_at, now=datetime.utcnow())

    @property
    def message_groups(self) -> List[MessageGroup]:
        groups = []

        if not self.messages:
            return groups

        curr = MessageGroup(self.messages[0].author)

        for index, message in enumerate(self.messages):
            next_index = index + 1 if index + 1 < len(self.messages) else index
            next_message = self.messages[next_index]

            curr.messages.append(message)

            if message.is_different_from(next_message):
                groups.append(curr)
                curr = MessageGroup(next_message.author)

        groups.append(curr)
        return groups

    def plain_text(self) -> str:
        messages = self.messages
        thread_create_time = self.created_at.strftime("%d %b %Y - %H:%M UTC")
        out = f"Thread created at {thread_create_time}\n"

        if self.creator == self.recipient:
            out += f"[R] {self.creator} "
            out += f"({self.creator.id}) created a Modmail thread. \n"
        else:
            out += f"[M] {self.creator} "
            out += "created a thread with [R] "
            out += f"{self.recipient} ({self.recipient.id})\n"

        out += "────────────────────────────────────────────────\n"

        if messages:
            for index, message in enumerate(messages):
                next_index = index + 1 if index + 1 < len(messages) else index
                curr, next_ = message.author, messages[next_index].author

                author = curr
                user_type = "M" if author.mod else "R"
                create_time = message.created_at.strftime("%d/%m %H:%M")

                base = f"{create_time} {user_type} "
                base += f"{author}: {message.raw_content}\n"

                for attachment in message.attachments:
                    base += f"Attachment: {attachment}\n"

                out += base

                if curr != next_:
                    out += "────────────────────────────────\n"
                    # current_author = author

        if not self.open:
            if messages:  # only add if at least 1 message was sent
                out += "────────────────────────────────────────────────\n"

            out += f"[M] {self.closer} ({self.closer.id}) "
            out += "closed the Modmail thread. \n"

            closed_time = self.closed_at.strftime("%d %b %Y - %H:%M UTC")
            out += f"Thread closed at {closed_time} \n"

        return out


class MinimalLogEntry:
    def __init__(self, data):
        self.key: str = data["key"]
        self.open: bool = data["open"]

        self.created_at: datetime = dateutil.parser.parse(data["created_at"])
        if self.created_at.tzinfo is not None:
            self.created_at = self.created_at.replace(tzinfo=None)

        self.human_created_at: str = duration(self.created_at, now=datetime.utcnow())
        self.closed_at: Optional[datetime] = (
            dateutil.parser.parse(data["closed_at"]) if not self.open else None
        )
        if self.closed_at is not None and self.closed_at.tzinfo is not None:
            self.closed_at = self.closed_at.replace(tzinfo=None)

        self.creator: Author = Author(data["creator"])
        self.recipient: Author = Author(data["recipient"])
        self.nsfw: Optional[bool] = data.get("nsfw")
        self.title: Optional[str] = data.get("title")
        self.last_message: Optional[Message] = (
            Message(data["last_message"]) if data.get("last_message") else None
        )
        self.message_count: int = data["message_count"]

    @property
    def human_closed_at(self) -> str:
        return duration(self.closed_at, now=datetime.utcnow())


class LogList:
    def __init__(self, data, prefix, page, max_page, status_open, count_all):
        logs = list()
        for log in data:
            logs.append(MinimalLogEntry(log))
        self.logs: list = logs
        self.prefix: str = prefix
        self.page: int = page
        self.max_page: int = max_page
        self.status_open: bool = status_open
        self.count_all: int = count_all


class Author:
    def __init__(self, data: AuthorPayload):
        self.id: int = int(data.get("id"))
        self.name: str = data["name"]
        self.discriminator: str = data["discriminator"]
        self.avatar_url: str = data["avatar_url"].split("?")[0] or data["avatar_url"]
        self.mod: bool = data["mod"]

    @property
    def default_avatar_url(self) -> str:
        return f"https://cdn.discordapp.com/embed/avatars/{int(self.id) % 5}.png"

    def __str__(self) -> str:
        return f"{self.name}" if self.discriminator == "0" else f"{self.name}#{self.discriminator}"

    def __eq__(self, other: Author) -> bool:
        return self.id == other.id and self.mod is other.mod


class MessageGroup:
    def __init__(self, author: Author):
        self.author: Author = author
        self.messages: List[Message] = []

    @property
    def created_at(self) -> str:
        return self.messages[0].human_created_at

    @property
    def type(self) -> str:
        return self.messages[0].type


class Attachment:
    def __init__(self, data: Union[str, AttachmentPayload]):
        if isinstance(data, str):  # Backwards compatibility
            self.id: int = 0
            self.filename: str = "attachment"
            self.url: str = data
            self.is_image: bool = True
            self.size: int = 0
        else:
            self.id = int(data["id"])
            self.filename: str = data["filename"]
            self.url: str = data["url"]
            self.is_image: bool = data["is_image"]
            self.size: int = data["size"]
            self.content_type: str = data["content_type"]

    @property
    def is_attachment_expired(self) -> bool:
        parsed_url = urlparse(self.url)
        query_params = parse_qs(parsed_url.query)
        expiry = int(query_params.get("ex", [None])[0], 16)
        current_time = time()
        return current_time > expiry


class Message:
    def __init__(self, data: MessagePayload, bot: ModmailBot = None):
        self.id: int = int(data["message_id"])
        self.created_at: datetime = dateutil.parser.parse(data["timestamp"])
        if self.created_at.tzinfo is not None:
            self.created_at = self.created_at.replace(tzinfo=None)
        self.attachments: List[Attachment] = [Attachment(a) for a in data["attachments"]]
        self.human_created_at: str = duration(self.created_at, now=datetime.utcnow())
        self.raw_content: str = data["content"]
        self.content: str = self.format_html_content(self.raw_content)
        self.author: Author = Author(data["author"])
        self.bot = bot
        self.type: str = data.get("type", "thread_message")
        self.edited: bool = data.get("edited", False)

    def is_different_from(self, other: Message) -> bool:
        return (
            (other.created_at - self.created_at).total_seconds() > 60
            or other.author != self.author
            or other.type != self.type
        )

    async def refresh_attachment_url(self, attachments: Attachment):
        if not self.bot or self.author.mod:
            return attachments
        user = cache["users"][self.author.id] if self.author.id in cache["users"] else None
        dm_channel = cache["dm_channels"][self.author.id] if self.author.id in cache["dm_channels"] else None
        discord_message = cache["messages"][self.id] if self.id in cache["messages"] else None
        update_attachments, to_save = False, []
        for i, attachment in enumerate(attachments):
            if not attachment.is_attachment_expired:
                continue
            if not user:
                user = self.bot.get_user(self.author.id) or await self.bot.fetch_user(self.author.id)
                cache["users"][self.author.id] = user
            if not dm_channel:
                dm_channel: DMChannel = user.dm_channel or await user.create_dm()
                cache["dm_channels"][self.author.id] = dm_channel
            try:
                if not discord_message:
                    discord_message = await user.dm_channel.fetch_message(self.id)
                    cache["messages"][self.id] = discord_message
                attachment.url = discord_message.attachments[i].url
                logger.debug(f"Refreshed Attachment#{i+1} for Message ID {self.id}")
                if not update_attachments:
                    update_attachments = True
            except Exception:
                logger.debug(f"Unable to find Message ID {self.id} in {user}'s DM")
                continue
            to_save.append(attachment.__dict__)
        if update_attachments and self.bot:
            await self.bot.db.logs.update_one(
                {"messages.message_id": str(self.id)}, {"$set": {"messages.$.attachments": to_save}}
            )
        return attachments

    @property
    async def valid_attachments(self) -> List[Attachment]:
        return await self.refresh_attachment_url(self.attachments)

    @staticmethod
    def format_html_content(content: str) -> str:
        return format_content_html(content)
