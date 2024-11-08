
from config import TOKEN

import os
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from gtts import gTTS
from deep_translator import GoogleTranslator
import random


# Укажите ваш токен
BOT_TOKEN = TOKEN

# Инициализация объектов
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Создаем папку для сохранения аудио
if not os.path.exists('audio'):
    os.makedirs('audio')


# Получение текста от пользователя
@router.message(lambda message: message.text is not None)
async def handle_text(message: Message):
    user_text = message.text

    # Ответ с текстом
    await message.reply(f"Вы написали: {user_text}")

    # Создаем inline-клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перевести на английский",
                    callback_data=f"translate:{user_text}"
                ),
                InlineKeyboardButton(
                    text="Сделать голосовое",
                    callback_data=f"voice:{user_text}"
                ),
            ]
        ]
    )

    # Отправляем клавиатуру
    await message.reply("Выберите действие:", reply_markup=keyboard)


# Обработчик для кнопки "Перевести на английский"
@router.callback_query(lambda callback: callback.data.startswith("translate:"))
async def translate_text(callback: CallbackQuery):
    # Получаем текст из callback_data
    user_text = callback.data.split("translate:")[1]
    translated = GoogleTranslator(source='auto', target='en').translate(user_text)

    # Отправляем перевод
    await callback.message.reply(f"Перевод:\n{translated}")
    await callback.answer()  # Убираем "часики" на кнопке


# Обработчик для кнопки "Сделать голосовое"
@router.callback_query(lambda callback: callback.data.startswith("voice:"))
async def text_to_voice(callback: CallbackQuery):
    # Получаем текст из callback_data
    user_text = callback.data.split("voice:")[1]
    file_path = f"audio/{callback.id}.mp3"

    # Список доступных языков для озвучки
    languages = ['en', 'ru', 'de', 'fr', 'it', 'es', 'zh-cn']

    # Случайный выбор языка
    random_lang = random.choice(languages)
    print(f"Selected language: {random_lang}")  # Для отладки, можно убрать

    # Генерация голосового сообщения
    tts = gTTS(user_text, lang=random_lang)  # Используем случайно выбранный язык
    tts.save(file_path)

    # Отправка голосового сообщения
    voice = FSInputFile(file_path)
    await bot.send_voice(chat_id=callback.message.chat.id, voice=voice)

    # Удаляем файл после отправки (опционально)
    os.remove(file_path)
    await callback.answer()  # Убираем "часики" на кнопке


# Основная функция для запуска бота
async def main():
    print("Бот запущен...")
    dp.include_router(router)  # Добавляем маршрутизатор в диспетчер
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
