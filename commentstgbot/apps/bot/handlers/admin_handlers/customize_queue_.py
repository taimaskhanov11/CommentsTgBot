from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from loguru import logger
from telethon import TelegramClient

from commentstgbot.apps.bot import markups
from commentstgbot.apps.bot.filters.admin_filters import AdminPrivateFilter
from commentstgbot.apps.bot.utils.queue_helpers import send_current_queues
from commentstgbot.apps.controller.classes import Request
from commentstgbot.config.config import config
from commentstgbot.db.db_main import temp
from commentstgbot.loader import bot


class AddPostGroupStates(StatesGroup):
    add = State()


async def customize_queue_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await send_current_queues(message)
    await message.answer(
        "При добавлении нового поста автоматически удалиться самый первый в очереди, если очередь заполнена",
        reply_markup=markups.add_post_keyboard,
    )


async def add_post_start(call: types.CallbackQuery):
    await call.message.answer("Перешлите пост из канала")
    await AddPostGroupStates.first()


async def add_post(message: types.Message, state: FSMContext):
    try:
        request = Request.parse(message)
        logger.info(request)
        if request:
            # temp.current_posts.append(request)
            await bot.forward_message(config.bot.chat, request.from_id, request.message_id)
            await message.answer("Пост успешно добавлен")
            await state.finish()
        else:
            await message.answer("Не удалось добавить пост, проверьте правильность введенных данных")
    except Exception as e:
        await message.answer("Перешлите сообщение из канала если чат закрыт добавьте аккаунт в канал")
        logger.critical(e)


async def delete_post(call: types.CallbackQuery):
    try:
        # message_ids = call.data[12:]
        await call.message.delete()
        print(call.data)
        _, _, channel_id, channel_post = call.data.split('_')
        channel_id = int(channel_id)
        channel_post = int(channel_post)
        for num, r in enumerate(temp.current_posts):
            if (channel_id, channel_post) == r:
                try:
                    client: TelegramClient = config.controller.controller.client
                    # todo 08.04.2022 21:18 taima: добавить проверку id, чтобы запускать в разны чатах
                    await client.delete_messages(config.bot.chat, r.message_id)
                    # await r.message.delete()
                except Exception as e:
                    logger.critical(e)
                temp.current_posts.remove((channel_id, channel_post))
                await call.message.answer(f"Пост {(channel_id, channel_post)} успешно удален")
                logger.info(f"Пост {(channel_id, channel_post)} удален")
                break
        # if url in temp.current_posts:
        #     temp.current_posts.remove(url)
        #     await call.message.answer("Пост успешно удален")
        #     logger.info(f"Пост {url} удален")
        else:
            await call.message.answer("Пост не найден в очереди")
    except Exception as e:
        logger.exception(e)
        await call.message.answer("Пост не найден в очереди")


def register_customize_queue_handlers(dp: Dispatcher):
    dp.register_message_handler(customize_queue_menu, AdminPrivateFilter(), text_startswith="🔩", state="*")
    dp.register_callback_query_handler(delete_post, AdminPrivateFilter(), text_startswith="delete_post")
    dp.register_callback_query_handler(add_post_start, AdminPrivateFilter(), text_startswith="add_post")
    dp.register_message_handler(add_post, AdminPrivateFilter(), state=AddPostGroupStates)
