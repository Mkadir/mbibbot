from aiogram import executor
from pyrogram.raw.types import PeerChat
from pyrogram.utils import get_peer_type
from loader import dp, bot, app
import middlewares, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands
from data.config import GROUP_ID
from pyrogram import Client, enums, filters, types


async def on_startup(dispatcher):
    await set_default_commands(dispatcher)
    await on_startup_notify(dispatcher)

    # await app.connect()
    # member = await app.get_chat_member(GROUP_ID, 1295486091)
    # print(member)


if __name__ == '__main__':
    # app.run()
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
