from aiogram import Dispatcher, types
from aiogram.types import ChatType
from loguru import logger

from commentstgbot.apps.bot.filters.admin_filters import AdminSuperGroupFilter
from commentstgbot.apps.bot.filters.common_menu_filters import PostLinkFilter
from commentstgbot.apps.bot.utils.message_processes import message_controller
from commentstgbot.apps.bot.utils.request_helpers import send_check_request
from commentstgbot.apps.controller.checker import VkChecker
from commentstgbot.apps.controller.classes import Request, Response
from commentstgbot.config.answer import answer
from commentstgbot.config.config import config
from commentstgbot.db.db_main import temp, redis
# todo 19.03.2022 13:30 taima: удаление сообщений после определенного времени
# todo 19.03.2022 13:33 taima: проверять какие задания выполнены какие нет
# todo 19.03.2022 12:47 taima:
from commentstgbot.loader import bot


# @logger.catch
async def all_text(message: types.Message, new_request: Request):
    try:
        logger.trace(temp.current_posts)
        # Отправка запросов на проверку лайка или комментария
        async with VkChecker(config.vk.token) as vk_checker:

            # Получение проверяемого пользователя

            checker_user = await vk_checker.is_other_user(message.text) or new_request.like.owner_id

            if not checker_user:
                await message_controller(
                    message,
                    "Ошибка при проверке пользователя\n."
                    "Проверьте что ссылка через !! ведена правильно,"
                    " и ведет на страницу пользователя, а не группы",
                )
                return

            # Проверка доступности
            logger.debug(f"Проверка доступности поста {new_request}")
            if not await vk_checker.is_access(checker_user, config.bot.check_type, new_request):
                await message_controller(message, answer.common.no_access)

            else:
                # Если пользователь имеет вип статус, игнорируем проверку и сразу добавляем
                if message.from_user.id in config.bot.vip:
                    await redis.incr("post_count")
                    temp.current_posts.append(new_request)
                    return

                try:
                    unfinished_tasks: tuple[Response] = await send_check_request(checker_user, vk_checker)
                except Exception as e:
                    logger.warning(e)
                    await message_controller(message, answer.common.no_access)
                    return
                    # Если лайк или комментарий не найден
                if unfinished_tasks:
                    unfulfilled_s = answer.common.check_failed
                    # todo 19.03.2022 14:37 taima: enumarate
                    for num, task in enumerate(unfinished_tasks, 1):
                        # todo 19.03.2022 21:25 taima: пофиксить проверку
                        unfulfilled_s += f"{num}. {task.unfulfilled}\n"
                    # await message.answer(unfulfilled_s, disable_web_page_preview=True)
                    await message_controller(message, unfulfilled_s, disable_web_page_preview=True)

                # Если лайк или комментарий найден добавляем в список
                else:
                    # await message.edit_text(message.text, disable_web_page_preview=True)
                    logger.success(f"Успешно добавлен в список {new_request}")
                    await redis.incr("post_count")
                    temp.current_posts.append(new_request)

    except Exception as e:
        await message_controller(message, answer.common.no_access)
        logger.exception(e)
        for admin in config.bot.admins:
            await bot.send_message(admin, f"{answer.common.error}\n{message.text}")
        # await message_controller(message, answer.common.error)


async def admin_text(message: types.Message):
    logger.info(f"Админ {message.from_user.id}|{message}")
    pass


def register_common_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_text, AdminSuperGroupFilter(), chat_type=ChatType.SUPERGROUP)
    dp.register_message_handler(all_text, PostLinkFilter(), chat_type=ChatType.SUPERGROUP)
