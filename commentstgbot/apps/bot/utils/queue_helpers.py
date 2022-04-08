from aiogram import types

from commentstgbot.apps.bot import markups
from commentstgbot.db.db_main import temp


async def send_current_queues(message: types.Message):
    await message.answer("Текущая очередь:\n")
    for num, r in enumerate(temp.current_posts, 1):
        await message.answer(f"{num}. {r.text}", reply_markup=markups.get_queue_keyboard(r.channel_id, r.channel_post))
