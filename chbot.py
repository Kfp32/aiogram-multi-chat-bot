import asyncio
import logging
import random
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from src.chat import Chat
from database import DataBase
from aiogram.fsm.storage.memory import MemoryStorage

db = DataBase()

logger = logging.getLogger("bbot")

running_bots = {}

async def start_pet_bot(token: str):
    """Start polling for a child bot using a given token."""
    if token in running_bots:
        logger.warning(f"The bot with the {token} token is already running.")
        return

    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    chats = []

    async def get_name():
        me = await bot.get_me()
        return me.username

    def get_mess(chat):
        N = random.randint(db.get_min_mes(token), db.get_max_mes(token))
        message = ""
        available_messages = chat.get_mess()
        if not available_messages:
            return "No messages to generate from."
        for i in range(N):
            temp = random.choice(available_messages)
            message += f"{temp} "
        return message.strip()

    def add_chat(chat_id):
        chat = Chat(chat_id)
        chats.append(chat)
        return chat

    def get_chat(chat_id):
        for chat in chats:
            if chat.chat_id == chat_id:
                return chat
        return add_chat(chat_id)

    @dp.message()
    async def omg(message: Message) -> None:
        logger.info(f"Message received from {message.from_user.username}: {message.text}")
        if message.chat.type == "private":
            logger.info("Message not in chat!")
            return

        chat = get_chat(message.chat.id)
        logger.info(f"Processing chat with ID: {message.chat.id}")

        chat.add_mess(message.text)
        logger.info(f"The message has been added to the chat list. Current list of messages: {chat.get_mess()}")

        if message.reply_to_message is not None and message.reply_to_message.from_user.id == bot.id:
            await bot.send_message(chat_id=message.chat.id, text=get_mess(chat))
            return

        cooldown = int(db.get_couldown(token))
        if chat.now_mes + 1 >= cooldown:
            generated_message = get_mess(chat)
            logger.info(f"Reached cooldown. Send a message: {generated_message}")
            await bot.send_message(chat_id=message.chat.id, text=generated_message)
            chat.now_mes = 0
        else:
            chat.now_mes += 1
            logger.info(f"Current number of messages before cooldown: {chat.now_mes}")

    async def on_startup(dispatcher):
        await bot.delete_webhook()

    async def run():
        await dp.start_polling(bot, on_startup=on_startup)

    task = asyncio.create_task(run())
    running_bots[token] = task
    await asyncio.sleep(0)

async def stop_pet_bot(token: str):
    """Stops polling for a child bot using a given token."""
    task = running_bots.pop(token, None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info(f"Polling stopped for bot with token {token}")
    else:
        logger.warning(f"The bot with the {token} token was not found among the running ones.")
