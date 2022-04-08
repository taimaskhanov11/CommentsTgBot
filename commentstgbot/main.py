import asyncio
import logging

from aiogram import Bot
from aiogram.types import BotCommand
from loguru import logger

from commentstgbot.apps.bot.handlers.admin_handlers.admin_commands import register_admin_commands_handlers
from commentstgbot.apps.bot.handlers.admin_handlers.bot_settings import register_bot_settings_handlers
from commentstgbot.apps.bot.handlers.admin_handlers.customize_queue_ import register_customize_queue_handlers
from commentstgbot.apps.bot.handlers.admin_handlers.privilege_settings import register_privilege_handlers
from commentstgbot.apps.bot.handlers.errors_handlers import register_error_handlers
from commentstgbot.apps.bot.middleware.auth_middleware import AuthMiddleware
from commentstgbot.apps.controller.controller import Controller
from commentstgbot.config.config import config
from commentstgbot.config.log_settings import init_logging
from commentstgbot.loader import bot, dp, scheduler


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/admin", description="Админ меню"),
    ]
    await bot.set_my_commands(commands)


# todo 01.04.2022 1:08 taima:  tzlocal, scheduler
# todo 01.04.2022 15:29 taima: F, Q tortoise;atomic;
async def main():
    # Настройка логирования
    init_logging(old_logger=True, level="TRACE", old_level=logging.INFO, steaming=True, write=False)
    logger.info(f"Starting bot {(await bot.get_me()).username}")

    # Установка команд бота
    await set_commands(bot)

    # Меню админа
    # register_admin_commands_handlers(dp)

    # Регистрация хэндлеров
    register_admin_commands_handlers(dp)
    register_bot_settings_handlers(dp)
    register_customize_queue_handlers(dp)
    register_privilege_handlers(dp)
    # register_common_handlers(dp)
    register_error_handlers(dp)
    # Регистрация middleware
    # dp.middleware.setup(TestMiddleware())
    # dp.middleware.setup(AuthMiddleware())
    # todo 19.03.2022 17:42 taima:
    # dp.middleware.setup(ThrottlingMiddleware(limit=0.5))

    # Регистрация фильтров
    # dp.filters_factory.bind(chat_type=ChatType.PRIVATE, user_id=config.bot.admins,event_handlers=admin_start )

    # asyncio.create_task(message_delete_worker())
    # scheduler.add_job(views_update, trigger="cron", hour=0, minute=0, second=0)
    # logger.info(f"Количество задач")
    # for j in scheduler.get_jobs():
    #     logger.info(j)
    # # Запуск поллинга
    # # await dp.skip_
    # # updates()  # пропуск накопившихся апдейтов (необязательно)
    # scheduler.start()
    controller = Controller(**config.controller.dict())
    config.controller.controller = controller
    asyncio.create_task(controller.start())
    scheduler.start()
    await dp.skip_updates()
    await dp.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.get_event_loop()
