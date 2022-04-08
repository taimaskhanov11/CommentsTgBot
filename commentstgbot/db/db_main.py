import asyncio
import collections
from collections import deque

from aiogram import types
from pydantic import BaseModel

from commentstgbot.apps.controller.classes import Request
from commentstgbot.config.config import config


class DelMessage(BaseModel):
    chat_id: int
    message_id: int
    user_id: int


class temp:
    current_posts: deque[Request] = deque(maxlen=config.settings.queue_length)


class DummyRedis:
    storage = collections.defaultdict(int)

    async def get(self, key):
        return self.storage.get(key)

    async def incr(self, key):
        self.storage[key] += 1

    async def getset(self, key, value):
        old_val = self.storage.get(key)
        self.storage[key] = value
        return old_val

redis = (
    DummyRedis()
)
