import asyncio
import os
import time
import base64
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

load_dotenv()

client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
db = client['ovkuse']
users_collection = db['users']

bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

translations = {
    "ru": {
        "start_message": "Привет, @{username}! 👋",
        "button_text": "Погнали! 🚀"
    },
    "en": {
        "start_message": "Hello, @{username}! 👋",
        "button_text": "Let's go! 🚀"
    },
    "uk": {
        "start_message": "Привіт, @{username}! 👋",
        "button_text": "Почнемо! 🚀"
    }
}

def get_translation(language_code: str, key: str, **kwargs):
    lang = translations.get(language_code, translations["en"])
    return lang[key].format(**kwargs)

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    language_code = message.from_user.language_code
    profile_pictures = await bot.get_user_profile_photos(message.from_user.id)

    file_id = dict((profile_pictures.photos[0][0])).get("file_id")
    file = await bot.get_file(file_id)

    file_content = await bot.download_file(file.file_path)
    base64_photo = base64.b64encode(file_content.getvalue()).decode('utf-8')

    print(file)


    await users_collection.update_one(
        {'_id': user_id},
        {
            '$setOnInsert': {
                'favorites': []
            },
            '$set': {
                'username': message.from_user.username,
                'photo_base64': base64_photo
            }
        },
        upsert=True 
    )

    start_message = get_translation(language_code, "start_message", username=message.from_user.username)
    button_text = get_translation(language_code, "button_text")

    await message.answer(start_message, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_text, web_app=WebAppInfo(url="https://tastemates.vercel.app/"))]
    ]))
    

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')