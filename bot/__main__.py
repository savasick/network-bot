import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from bot.config import config
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from datetime import timedelta, datetime
import sqlite3

bot_token = config.BOT_TOKEN.get_secret_value()
admin = config.ADMIN_ID
path_scan="net_devs.db"
logging.basicConfig(level=logging.INFO)

bot = Bot(bot_token, parse_mode="HTML")
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info("Received start command from user %s", message.from_user.id)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text=str("/were")))
    builder.add(types.KeyboardButton(text=str("/online")))
    chat = await bot.get_chat(message.from_user.id)
    user_info = f"Username: {chat.username}, First Name: {chat.first_name}, Last Name: {chat.last_name}, ID: {chat.id}"
    await message.answer(f"Here is your information:\n{user_info}", reply_markup=builder.as_markup(resize_keyboard=True))


def get_devices_data(source):
    conn = sqlite3.connect(path_scan)
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {source}')
    devices = cursor.fetchall()
    conn.close()
    return devices

@dp.message(Command("online"))
async def cmd_info(message: types.Message):
    if message.from_user.id == admin:
        logging.info("Received devices command from user %s", message.from_user.id)
        devices = get_devices_data('devices')
        if devices:
            formatted_devices = "\n".join([f"MAC Address: {mac_address}\n IP Address: {ip_address}\n Manufacturer: {manufacturer}\n Custom Name: {custom_name}\n\n" for mac_address, ip_address, manufacturer, custom_name in devices])
            await message.answer(f"Here is your information:\n{formatted_devices}")
        else:
            logging.warning("No devices found.")
            await message.answer("No devices found.")
    else:
        #ban_duration = timedelta(hours=1)
        #await bot.ban_chat_member(message.chat.id, message.from_user.id, until_date=int((datetime.now() + ban_duration).timestamp()))
        await message.answer("You don't have access to this command.")

@dp.message(Command("were"))
async def cmd_info(message: types.Message):
    if message.from_user.id == admin:
        logging.info("Received previous command from user %s", message.from_user.id)
        devices = get_devices_data('previous_devices')
        if devices:
            formatted_devices = "\n".join([f"MAC Address: {mac_address}\n IP Address: {ip_address}\n Manufacturer: {manufacturer}\n Custom Name: {custom_name}\n\n" for mac_address, ip_address, manufacturer, custom_name in devices])
            await message.answer(f"Here is your information:\n{formatted_devices}")
        else:
            logging.warning("No devices found.")
            await message.answer("No devices found.")
    else:
        #ban_duration = timedelta(hours=1)
        #await bot.ban_chat_member(message.chat.id, message.from_user.id, until_date=int((datetime.now() + ban_duration).timestamp()))
        await message.answer("You don't have access to this command.") 


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
