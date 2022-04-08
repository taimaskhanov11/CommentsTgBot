import typing
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel
from telethon import TelegramClient

BASE_DIR = Path(__file__).parent.parent.parent


def load_yaml(file) -> dict:
    with open(Path(BASE_DIR, file), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
def load_arg_yaml(file) -> dict:
    with open(Path(BASE_DIR, f"{file}.yml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class Bot(BaseModel):
    token: str
    id: int
    admin: Optional[list[int]]
    vip: Optional[list[int]]
    chat: Optional[int]
    # chat: Optional[list[int]]


class Controller(BaseModel):
    api_id: int
    api_hash: str
    controller: Optional[TelegramClient]

    class Config:
        arbitrary_types_allowed = True


class Settings(BaseModel):
    check_type: typing.Literal["like", "comment", "like_comment"]
    queue_length: int
    dd_messages: int


class Config(BaseModel):
    bot: Bot
    controller: Controller
    settings: Settings


config = Config(**load_yaml("config_dev.yml"))
