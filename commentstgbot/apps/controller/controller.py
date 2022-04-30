import asyncio
from pathlib import Path
from typing import Optional

import aiohttp
from loguru import logger
from pydantic import BaseModel
from telethon import TelegramClient, events
# client = TelegramClient(f'_session', api_id, api_hash)
from telethon.tl import patched, types

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
        # self.client = TelegramClient(path, config.controller.api_id, config.controller.api_hash)
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
            logger.info(message)
            # logger.info(message.chat_id)
            try:
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
                                             f"@{user.username}, Перешлите сообщение из канала если чат закрыт добавьте меня в канал")
                    return

                # проверка на канал
                if not await self.checker.is_channel(message):
                    await message_controller(message,
                                             f"@{user.username}, Перешлите сообщение из канала если чат закрыт добавьте меня в канал")
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
                                             f"@{user.username}, Нет доступа к каналу, добавьте меня в канал")
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
            except Exception as e:
                await message_controller(message,
                                         f"Нет доступа к каналу, добавьте меня в канал и перешлите пост от своего лица")
                logger.critical(e)
                raise e

            temp.current_posts.append(request)

        while True:
            await self.client.run_until_disconnected()

    async def dummy_start(self):
        # await self._init()
        path = str(Path(SESSION_PATH, f"{config.controller.api_id}.session"))
        self.client = TelegramClient(path, config.controller.api_id, config.controller.api_hash)
        await self.client.start()

        # exit()

        @self.client.on(events.NewMessage(incoming=True))
        async def common_handler(event: events.NewMessage.Event):
            message: patched.Message = event.message
            print(message)
            print(message.from_id.user_id)
            print(message.from_id)

        lst = [
            "https://sun7-8.userapi.com/impf/jcVohqBM7w21KRIJRxGiPAUVepdoJPTQkMENhQ/yDZs1REt-mQ.jpg?size=750x746&quality=95&sign=8bf6b9f499f1b4e3e83d6eea1186991e&c_uniq_tag=axlsc99uKkpOUAthcA3YlP5391MEsnoHK6ql5RY6n74&type=album",
            # "https://sun7-9.userapi.com/impf/NlUvHWpjdV_atneeDnY0RW6RyAspNXa6IzFETw/_u0fZFTM-4U.jpg?size=750x1000&quality=95&sign=7bdcfa4b7e660ef7e601de149f0dd49b&c_uniq_tag=3evecVFqh_HLaQAOGSD_IiOX1VnQvlUC5A4UleKJA-c&type=album",
            # "https://sun7-6.userapi.com/impf/cTGkU6Sr3LwjSWm2k9aZTcUF-8PRemr5X2lp0A/Jden1dv7Ho0.jpg?size=564x1002&quality=95&sign=89dd021bb5e106d0a30c9979af895fae&c_uniq_tag=UP8iXd3w4hjlhihAAyvIlr_ZHFZGbSR624AHmo_pXDk&type=album"
        ]

        print(await self.client.get_entity(5274127894))
        # photos_bytes = []
        # for i in lst:
        #     photos_bytes.append(await download_photo(i))
        # for i in :
        #
        # await self.client.send_file("@mumyau", ["music.mp3",photos_bytes[0]], caption="Бла бла")

        # await self.client.send_file("@mumyau",photos_bytes[0], caption="Бла бла")
        # user: User = await self.client.get_entity(1985947355)
        # await self.client.send_file(1985947355,(photos=lst, users=[user]))
        # await self.client.send_message(1985947355,"Бла бла", file=lst[0] )
        # await self.client.send_message(1985947355,"Бла бла", file=lst[0] )
        exit()


headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/99.0.4844.51 Safari/537.36"
}


async def download_photo(url):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as res:
            return await res.read()


if __name__ == "__main__":
    pass
    controller = Controller(**config.controller.dict())
    # init_logging(old_logger=True, level="TRACE", old_level=logging.INFO, steaming=True, write=False)
    # asyncio.get_event_loop().run_until_complete(controller.start())
    # controller.start()

    asyncio.get_event_loop().run_until_complete(controller.dummy_start())
