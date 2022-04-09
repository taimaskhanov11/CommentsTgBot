import asyncio
from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic import BaseModel
from telethon import TelegramClient, events, functions
# client = TelegramClient(f'_session', api_id, api_hash)
from telethon.tl import patched, types
from telethon.tl.functions.channels import GetParticipantRequest

from commentstgbot.apps.bot.utils.message_processes import message_controller, add_to_delete
from commentstgbot.apps.controller.checker import Checker
from commentstgbot.apps.controller.classes import Request, Response
from commentstgbot.config.config import config
from commentstgbot.db.db_main import temp

SESSION_PATH = Path(Path(__file__).parent, "sessions")


class Controller(BaseModel):
    api_id: int
    api_hash: str
    client: Optional[TelegramClient]
    checker: Optional[Checker]

    class Config:
        arbitrary_types_allowed = True

    # todo 06.04.2022 21:10 taima: проверить на ошибку при бане

    async def check_request(self, checker_user) -> tuple[Optional[Response]]:
        tasks = []
        logger.debug(f"{checker_user} -> Отправка запросов на проверку")
        for request in temp.current_posts:
            task = asyncio.create_task(self.checker.send_request(checker_user, request, config.settings.check_type))
            tasks.append(task)

        result = await asyncio.gather(*tasks)
        logger.debug(f"Весь результат|{result}")
        not_done_response: tuple[Optional[Response], ...] = tuple(filter(lambda x: not bool(x), result))
        logger.debug(f"Не выполненные задачи|{not_done_response}")
        return not_done_response

    async def _init(self):
        logger.info("Запуск контроллера")
        path = str(Path(SESSION_PATH, f"{config.controller.api_id}.session"))
        self.client = TelegramClient(path, config.controller.api_id, config.controller.api_hash)
        self.checker = Checker(client=self.client)
        await self.client.start()

    async def start(self):
        await self._init()

        # todo 08.04.2022 13:46 taima: доработать изменени id группы
        @self.client.on(events.NewMessage(incoming=True, chats=config.bot.chat))
        # @self.client.on(events.NewMessage(incoming=True, ))
        async def common_handler(event: events.NewMessage.Event):
            # async def common_handler(message: patched.Message):
            message: patched.Message = event.message
            # logger.info(message)
            # logger.info(message.chat_id)

            checker_user_id = message.from_id.user_id
            user: types.User = await self.client.get_entity(checker_user_id)
            if user.id == config.bot.id:
                logger.info(f"Создано из бота {user}")
                request = Request.parse(message)
                temp.current_posts.append(request)
                return

                # print(message.id)
            # await self.client.forward_messages(message.chat_id, message)
            # await self.client.send_message(message.chat_id, "common_handler")
            # logger.info(message.fwd_from.channel_post)
            # проверка на админа
            if checker_user_id in config.bot.admin:
                logger.info(f"Админ {checker_user_id}|{message}")
                return

            # проверка на пересылку
            if not message.forwards:
                await message_controller(message,
                                         f"@{user.username}, Перешлите сообщение из канала если чат закрыт добавьте аккаунт в канал")
                return

            # проверка на канал
            if not await self.checker.is_channel(message):
                await message_controller(message,
                                         f"@{user.username}, Перешлите сообщение из канала если чат закрыт добавьте аккаунт в канал")
                return

            request = Request.parse(message)
            # logger.info(request)
            # проверка наличия
            if request in temp.current_posts:
                await message_controller(message,
                                         f"@{user.username}, Такой пост уже есть в списке, подождите пока пройдет 5")
                return

            # проверка доступа
            if not await self.checker.is_access(request, config.settings.check_type):
                await message_controller(message,
                                         f"@{user.username}, Нет доступа к каналу, добавьте аккаунт в канал")
                return

            # проверка на випа
            if checker_user_id not in config.bot.vip:
                logger.debug(f"Проверка {checker_user_id}")

                # проверка наличия комментария
                unfinished_tasks: tuple[Response] = await self.check_request(checker_user_id)
                if unfinished_tasks:
                    await message_controller(message, f"@{user.username}, Оставьте комментарии под постами ниже ⬇")
                    for r in unfinished_tasks:
                        f = await self.client.forward_messages(message.chat_id, r.message_id, message.chat_id)
                        add_to_delete(f)

                    # f_messages = await self.client.forward_messages(message.chat_id,
                    #                                                 [r.message_id for r in unfinished_tasks],
                    #                                                 message.chat_id)

                    # add_to_delete(f_messages)
                    return
            else:
                logger.debug(f"Vip, пропуск проверки {checker_user_id}")
            temp.current_posts.append(request)

        await self.client.run_until_disconnected()

    async def dummy_start(self):
        await self._init()

        @self.client.on(events.NewMessage(incoming=True))
        async def common_handler(event: events.NewMessage.Event):
            message: patched.Message = event.message
            await self.client.forward_messages(269019356, message)
            participant = await self.client(
                GetParticipantRequest(channel=event.original_update.message.to_id.channel_id,
                                      participant=event.original_update.message.from_id))
            print(participant)
            print(participant.participant)

        # chat_id = -1001750145969
        group = 1750145969
        chat_id2 = 1756454892
        # channel: types.Channel = await self.client.get_entity(chat_id)
        channel2: types.Channel = await self.client.get_entity(chat_id2)
        # print(channel)
        print(channel2)
        # functions.channels.
        result: types.channels.ChannelParticipants = await self.client(functions.channels.GetParticipantsRequest(
            channel=chat_id2,
            filter=types.ChannelParticipantsRecent(),
            offset=42,
            limit=20,
            hash=0
        ))
        print(result)
        print(result.users)
        functions.channels.get
        # group_name = "https://t.me/garitokenofficial"
        # group: types.Chat = await self.client.get_entity(group_name)
        # print(group)
        # print(group)
        # pprint(await self.client.)
        # await self.client.run_until_disconnected()


if __name__ == "__main__":
    pass
    controller = Controller(**config.controller.dict())
    # init_logging(old_logger=True, level="TRACE", old_level=logging.INFO, steaming=True, write=False)
    # asyncio.get_event_loop().run_until_complete(controller.start())
    # controller.start()

    asyncio.get_event_loop().run_until_complete(controller.dummy_start())
