import asyncio
import typing

import aiogram
import telethon
from loguru import logger
from pydantic import BaseModel
#
from telethon import TelegramClient
from telethon.tl import patched, types


class Request(BaseModel):
    channel_id: int
    channel_post: int
    # message: patched.Message
    text: str
    message_id: int
    from_id: int

    def __eq__(self, other):
        if isinstance(other, Request):
            return (self.channel_id == other.channel_id
                    and self.channel_post == other.channel_post)
        elif isinstance(other, tuple):
            return (self.channel_id == other[0]
                    and self.channel_post == other[1])
        return False

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def parse(cls, message: patched.Message | aiogram.types.Message):
        if isinstance(message, patched.Message):
            return cls(
                channel_id=message.fwd_from.from_id.channel_id,
                channel_post=message.fwd_from.channel_post,
                message_id=message.id,
                text=message.text,
                # message=message,
                from_id=message.from_id.user_id,
            )
        elif isinstance(message, aiogram.types.Message):
            return cls(
                channel_id=message.forward_from_chat.id,
                channel_post=message.forward_from_message_id,
                text=message.text,
                message_id=message.message_id,
                from_id=message.from_user.id
            )


class Response(Request):
    # is_commented: bool
    # is_subscribed: bool
    is_successfully: bool

    def __bool__(self):
        return self.is_successfully




if __name__ == "__main__":
    b = CommentRequest(type="photo", owner_id=1, item_id=1, photo_id=1)
    print(b.dict(exclude_defaults=False))
    print(b.photo_id)
    b.photo_id = 2
