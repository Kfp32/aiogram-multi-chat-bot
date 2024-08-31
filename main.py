import os
import logging
import asyncio

from aiogram import exceptions
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from src.database import DataBase
from aiogram.types import (Message, InlineKeyboardMarkup, InlineKeyboardButton)
from src.chbot import start_pet_bot, stop_pet_bot
import re

db = DataBase()

load_dotenv()

logging.basicConfig(level=logging.INFO)

MAIN_BOT_TOKEN = os.getenv('TOKEN')

main_bot = Bot(token=MAIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
main_dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    waiting_for_token = State()
    max_mes = State()
    min_mes = State()
    couldown = State()
    
@main_dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.reply("Hello! My name is Oleg and I will help you create a simple chat bot for "
                        "keep your conversation moving. Type /newbot to add a new chatbot"
                        "or /mybots to configure already added ones.")

@main_dp.message(Command("newbot"))
async def newbot(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_for_token)
    await main_bot.send_message(chat_id=message.chat.id,
                                text="Great! Here are brief instructions for adding a bot:\n\n"
                                     "1. Write a private message to @BotFather for /newbot\n"
                                     "2. Follow his instructions, and then forward me the message that he will send you after receiving the bot\n\n"
                                     "*IMPORTANT:* before sending a message here, enter the command /mybots into @BotFather, select your bot in the window that appears, then Bot Settings"
                                     "->Group privacy and disable private mode if enabled.\n\nProfit!")

@main_dp.message(Command("mybots"))
async def mybots(message: Message, state: FSMContext):
    await state.clear()
    owner = db.get_owners_bots(message.chat.id)
    if len(owner) == 0:
        await message.reply("You haven't added a single bot yet! Please write /newbot.")
        return
    buttons = []
    for name, token in owner:
        button = InlineKeyboardButton(text="@"+str(name), callback_data=str(token))
        buttons.append(button)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await main_bot.send_message(chat_id=message.chat.id,
                                text="Select your bot below:",
                                reply_markup=keyboard)


@main_dp.message(Form.waiting_for_token)
async def add_newbot(message: Message, state: FSMContext) -> None:
    pattern = r'(\d+:[A-Za-z0-9_-]+)'
    match = re.search(pattern, message.text)
    token = match.group(1) if match else None

    if token is None:
        await message.reply("This is not a token!")
        return

    if db.get_bot(token):
        await message.reply("The bot has already been added!")
        return

    from src.chbot import start_pet_bot

    bot = None
    try:
        bot = Bot(token)
        me = await bot.get_me()
    except exceptions.TelegramUnauthorizedError:
        await message.reply("The token is invalid or the bot is blocked!")
        return
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")
        return
    finally:
        if bot:
            await bot.session.close()

    await start_pet_bot(token)
    await db.add_bot(message.chat.id, token)
    await message.reply("Great! Your bot has been added successfully. Please configure it in /mybots")
    await state.clear()



@main_dp.message(Form.waiting_for_token)
async def add_newbot(message: Message, state: FSMContext) -> None:
    pattern = r'(\d+:[A-Za-z0-9_-]+)'
    await state.clear()
    match = re.search(pattern, message.text)
    token = match.group(1) if match else None

    if token is None:
        await message.reply("This is not a token!")
        return

    if db.get_bot(token):
        await message.reply("The bot has already been added!")
        return

    from src.chbot import start_pet_bot

    bot = None
    try:
        bot = Bot(token)
        me = await bot.get_me()
    except exceptions.TelegramUnauthorizedError:
        await message.reply("The token is invalid or the bot is blocked!")
        return
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")
        return
    finally:
        if bot:
            await bot.session.close()

    await start_pet_bot(token)
    await db.add_bot(message.chat.id, token)
    await message.reply("Great! Your bot has been added successfully. Please configure it in /mybots")
    await state.clear()


@main_dp.message(Form.couldown)
async def could(message: Message, state: FSMContext):
    data = await state.get_data()
    token = data.get('token')
    if not message.text.isdigit():
        await main_bot.send_message(chat_id=message.chat.id,
                                    text="Send only a whole number!")
        return
    couldown = int(message.text)

    if couldown <= 0:
        await main_bot.send_message(chat_id=message.chat.id,
                                    text="Cooldown must be a positive number!")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="<- Back", callback_data=f"{token}|back2")]])
    db.set_couldown(token, couldown)
    await main_bot.send_message(chat_id=message.chat.id,
                                text="Data updated successfully.",
                                reply_markup=keyboard)
    await state.clear()


@main_dp.message(Form.min_mes)
async def set_max_mes(message: Message, state: FSMContext):
    data = await state.get_data()
    token = data.get('token')
    max_mes = db.get_max_mes(token)
    if not message.text.isdigit():
        await main_bot.send_message(chat_id=message.chat.id,
                                    text="Send only the number!")
        return

    min_mes = int(message.text)
    if min_mes > max_mes:
        await main_bot.send_message(chat_id=message.chat.id,
                                    text="The minimum value must be less than or equal to the maximum!")
        return

    if min_mes < 1:
        await main_bot.send_message(chat_id=message.chat.id,
                                    text="The minimum value must be a positive number!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="<- Back", callback_data=f"{token}|back2")]])
    db.set_min_mes(token, min_mes)
    await main_bot.send_message(chat_id=message.chat.id,
                                text="Data updated successfully.",
                                reply_markup=keyboard)
    await state.clear()



@main_dp.message(Form.max_mes)
async def set_max_mes(message: Message, state: FSMContext):
    data = await state.get_data()
    token = data.get('token')
    min_mes = db.get_min_mes(token)
    if not message.text.isdigit():
        await main_bot.send_message(chat_id=message.chat.id,
                                    text="Send only the number!")
        return

    max_mes = int(message.text)
    if max_mes < min_mes:
        await main_bot.send_message(chat_id=message.chat.id,
                                    text="The maximum value must be greater than or equal to the minimum!")
        return

    if max_mes > 10:
        await main_bot.send_message(chat_id=message.chat.id,
                                    text="The maximum value must be less than 10!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="<- Back", callback_data=f"{token}|back2")]])
    db.set_max_mes(token, max_mes)
    await main_bot.send_message(chat_id=message.chat.id,
                                text="Data updated successfully.",
                                reply_markup=keyboard)
    await state.clear()



@main_dp.callback_query()
async def settings(call: CallbackQuery, state: FSMContext):
    if call.data == "back1":
        await state.clear()
        owner = db.get_owners_bots(call.message.chat.id)

        if len(owner) == 0:
            await main_bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="You haven't added a single bot yet! Please write /newbot.",
                reply_markup=None)
            return

        buttons = []
        for name, token in owner:
            button = InlineKeyboardButton(text="@" + str(name), callback_data=str(token))
            buttons.append(button)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        new_text = "Select your bot below:"

        await main_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=new_text,
            reply_markup=keyboard)
        return
    arr = db.get_owners_bots(call.message.chat.id)
    tokens = []
    for name, token in arr:
        tokens.append(token)

    if call.data in tokens:
        max_mes = db.get_max_mes(call.data)
        min_mes = db.get_min_mes(call.data)
        cd = db.get_couldown(call.data)
        name = db.get_bot_name(call.data)

        buttons = [
            [InlineKeyboardButton(text="Change message size", callback_data=f"{call.data}|size")],
            [InlineKeyboardButton(text="Change send cooldown", callback_data=f"{call.data}|cd")],
            [InlineKeyboardButton(text="<- Back", callback_data=f"back1"),
             InlineKeyboardButton(text="Untie the bot 🗑", callback_data=f"{call.data}|del")]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await main_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Settings @{name}\n\n"
                 f"Current settings:\n"
                 f"*Maximum* message size: {max_mes} words\n"
                 f"*Minimum* message size: {min_mes} words\n"
                 f"Current *cooldown*: messages are sent once every {cd} messages\n\n"
                 f"Below you can select an option to change it:",
            reply_markup=keyboard
        )
        return
    data = call.data.split("|")
    data_token = data[0]
    data_setting = data[1]

    if data_setting == "back1":
        owner = db.get_owners_bots(call.message.chat.id)
        if len(owner) == 0:
            await main_bot.edit_message_text(chat_id=call.message.chat.id,
                                       message_id=call.message.message_id,
                                       text="You haven't added a single bot yet! Please write /newbot.")
            return
        buttons = []
        for name, token in owner:
            button = InlineKeyboardButton(text="@" + str(name), callback_data=str(data_token))
            buttons.append(button)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        await main_bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text="Select your bot below:",
                                    reply_markup=keyboard)


    if data_token not in tokens:
        return

    max_mes = db.get_max_mes(data_token)
    min_mes = db.get_min_mes(data_token)
    cd = db.get_couldown(data_token)
    name = db.get_bot_name(data_token)

    if data_setting == "size":
        buttons = [
            [InlineKeyboardButton(text="? Maximum", callback_data=f"{data_token}|max"),
             InlineKeyboardButton(text="? Minimum", callback_data=f"{data_token}|min")],
            [InlineKeyboardButton(text="Change send cooldown", callback_data=f"{data_token}|cd")],
            [InlineKeyboardButton(text="<- Back", callback_data=f"back1"),
             InlineKeyboardButton(text="Untie the bot 🗑", callback_data=f"{data_token}|del")]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await main_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Settings @{name}\n\n"
                 f"Current settings:\n"
                 f"*Maximum* message size: {max_mes} words\n"
                 f"*Minimum* message size: {min_mes} words\n"
                 f"Current *cooldown*: messages are sent once every {cd} messages\n\n"
                 f"Below you can select an option to change it:",
            reply_markup=keyboard)
        return


    if data_setting in ["max", "min", "cd"]:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text = "<- Назад", callback_data=f"{data_token}|back2"),]])
        match data_setting:
            case "max":
                await state.set_state(Form.max_mes)
                await state.update_data(token=data_token)
                await main_bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text="Please enter the new maximum message size in the chat:",
                                            reply_markup=keyboard)

            case "min":
                await state.set_state(Form.min_mes)
                await state.update_data(token=data_token)
                await main_bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text="Please enter a new minimum message size in chat:",
                                            reply_markup=keyboard)

            case "cd":
                await state.set_state(Form.couldown)
                await state.update_data(token=data_token)
                await main_bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text="Please enter a new cooldown for sending messages to the bot in the chat:",
                                            reply_markup=keyboard)
    if data_setting == "del":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Yes I'm sure", callback_data=f"{data_token}|yes")],
            [InlineKeyboardButton(text="<- Back", callback_data=f"{data_token}|back2")]])
        await main_bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=f"Are you sure you want to disable @{name}?",
                                        reply_markup=keyboard)
    if data_setting == "yes":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="<- Back", callback_data=f"back1"), ]]
        )
        await stop_pet_bot(data_token)
        db.del_bot(data_token)
        await main_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"@{name} was successfully untied! Use /newbot to link your bot again.",
            reply_markup=keyboard
        )
    if data_setting == "back2":
        buttons = [
            [InlineKeyboardButton(text="Change message size", callback_data=f"{data_token}|size")],
            [InlineKeyboardButton(text="Change send cooldown", callback_data=f"{data_token}|cd")],
            [InlineKeyboardButton(text="<- Back", callback_data=f"back1"),
             InlineKeyboardButton(text="Untie the bot 🗑", callback_data=f"{data_token}|del")]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await main_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Settings @{name}\n\n"
                 f"Current settings:\n"
                 f"*Maximum* message size: {max_mes} words\n"
                 f"*Minimum* message size: {min_mes} words\n"
                 f"Current *cooldown*: messages are sent once every {cd} messages\n\n"
                 f"Below you can select an option to change it:",
            reply_markup=keyboard
        )
        return


async def main():
    bot_task = asyncio.create_task(main_dp.start_polling(main_bot))

    tokens = await db.get_tokens()

    bot_tasks = [start_pet_bot(token) for token in tokens]

    await asyncio.gather(bot_task, *bot_tasks)

if __name__ == '__main__':
    asyncio.run(main())



