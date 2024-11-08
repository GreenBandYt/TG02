
from config import TOKEN

import os
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, FSInputFile
from aiogram.filters.command import Command
from deep_translator import GoogleTranslator

# Укажите ваш токен
BOT_TOKEN = TOKEN

# Инициализация объектов
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Создаем папку для сохранения фото
if not os.path.exists('img'):
    os.makedirs('img')


# Обработчик для сохранения фото
@router.message(lambda message: message.photo is not None)
async def save_photo(message: Message):
    photo = message.photo[-1]  # Берем фото в самом высоком разрешении
    file_name = f"img/{photo.file_id}.jpg"

    # Скачиваем файл
    file = await bot.get_file(photo.file_id)
    await bot.download(file, destination=file_name)

    await message.reply(f"Фото сохранено: {file_name}")


# Отправка голосового сообщения
@router.message(Command("voice"))
async def send_voice_message(message: Message):
    voice_file = "voice.ogg"  # Укажите путь к вашему .ogg файлу
    if os.path.exists(voice_file):
        voice = FSInputFile(voice_file)
        await bot.send_voice(chat_id=message.chat.id, voice=voice)
    else:
        await message.reply("Файл голосового сообщения не найден.")


# Перевод текста на английский язык
@router.message(lambda message: message.text is not None)
async def translate_text(message: Message):
    translated = GoogleTranslator(source='auto', target='en').translate(message.text)
    await message.reply(f"Перевод:\n{translated}")


# Основная функция для запуска бота
async def main():
    print("Бот запущен...")
    dp.include_router(router)  # Добавляем маршрутизатор в диспетчер
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
