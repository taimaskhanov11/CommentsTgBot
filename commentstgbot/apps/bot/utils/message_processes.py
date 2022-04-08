import datetime
from typing import Sequence

from loguru import logger
from telethon.tl import patched

from commentstgbot.config.config import config
from commentstgbot.db.db_main import redis
from commentstgbot.loader import scheduler


async def delete_message_task(message: patched.Message | list[patched.Message]):
    try:
        if isinstance(message, list):
            for m in message:
                logger.trace(f"Удаление {m.id}")

                await m.delete()
        else:
            logger.trace(f"Удаление {message.id}")
            await message.delete()

        logger.debug(f"Сообщение {message.id} успешно очищено")
    except Exception as e:
        logger.warning(f"Сообщение уже удалено|{e}")


def add_to_delete(m: patched.Message | Sequence[patched.Message]):
    scheduler.add_job(delete_message_task, 'date',
                      run_date=datetime.datetime.now() +
                               datetime.timedelta(seconds=config.settings.dd_messages),
                      args=(m,))


async def message_controller(message: patched.Message, answer: str, only_add=False):
    await message.delete()
    # new_message = await config.controller.controller.client.send_message(message.chat_id, answer)
    new_message = await message.reply(answer)
    add_to_delete(new_message)
    old_message = await redis.getset(f"message_{message.from_id.user_id}", new_message)
    if old_message:
        await delete_message_task(old_message)
