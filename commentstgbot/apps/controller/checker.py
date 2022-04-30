import asyncio
import typing

import telethon
from loguru import logger
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.tl import patched, types

from commentstgbot.apps.controller.classes import Request, Response


class Checker(BaseModel):
    client: TelegramClient

    class Config:
        arbitrary_types_allowed = True

    async def send_request(self,
                           checker_user_id,
                           request: Request,
                           check_type: typing.Literal["comment", "subscribe", "comment_subscribe"]
                           ) -> Response:

        is_liked, is_commented = True, True
        if check_type == "comment":
            is_commented = await self.is_commented(checker_user_id, request)
        elif check_type == "subscribe":
            is_subscribed = await self.is_subscribed(checker_user_id, request)
        else:
            s_liked, is_commented = await asyncio.gather(
                self.is_commented(checker_user_id, request.like),
                self.is_subscribed(checker_user_id, request.comment)
            )
            pass

        return Response(
            **request.dict(),
            # is_commented=is_commented,
            # is_subscribed=is_subscribed,
            # is_successfully=all((is_commented, is_subscribed))
            is_successfully=all((is_commented,))
        )

    async def is_subscribed(self, checker_user, request: Request) -> bool:
        logger.trace(f"Запрос is_subscribed|{checker_user}|{request}")

    async def is_commented(self, checker_user, request: Request) -> bool:
        logger.trace(f"Запрос is_commented|{checker_user}|{request}")
        async for message in self.client.iter_messages(entity=request.channel_id,
                                                       reply_to=request.channel_post,
                                                       limit=15):
            message: patched.Message = message
            if message.from_id:
                try:
                    if message.from_id.user_id == checker_user:
                        logger.success(f"{checker_user} комментарий найден")
                        return True
                except Exception as e:
                    logger.warning(e)
        logger.warning(f"{checker_user} -> {request.channel_id}|{request.channel_post} комментарий не найден")
        return False

    async def comment_access(self, request: Request):
        try:
            async for message in self.client.iter_messages(entity=request.channel_id,
                                                           reply_to=request.channel_post,
                                                           limit=1):
                logger.success(message)
                return True
            return True
        except Exception as e:
            logger.warning(f"Запрос is_access|{request.from_id}|{request}|Нет доступа {e}")
            return False

    async def subscribe_access(self, request: Request):
        try:
            pass
        except telethon.errors.rpcerrorlist.ChatAdminRequiredError as e:
            logger.warning(f"Не в списке админов|{request}|{e}")
            return False

    async def is_access(
            self, request: Request,
            check_type: typing.Literal["comment", "subscribe", "comment_subscribe"], ) -> bool:
        logger.trace(f"Запрос is_access|{request.from_id}|{request}")
        comment = True
        subscribe = True
        match check_type:
            case "comment":
                comment = await self.comment_access(request)
            case "subscribe":
                subscribe = await self.subscribe_access(request)
            case "comment_subscribe":
                comment, subscribe = asyncio.gather(
                    self.comment_access(request),
                    self.subscribe_access(request)
                )
        return comment and subscribe

    async def is_channel(self, message: patched.Message):
        if isinstance(message.fwd_from.from_id, types.PeerChannel):
            # todo 06.04.2022 21:41 taima:
            return True
        await message.delete()
        await self.client.send_message(message.chat_id, "Сообщение не из канала")
