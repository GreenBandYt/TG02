from config import TOKEN

import os
import random
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from gtts import gTTS

# Укажите ваш токен
BOT_TOKEN = TOKEN

# Инициализация объектов
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Создаем папки для сохранения файлов
if not os.path.exists('audio'):
    os.makedirs('audio')
if not os.path.exists('photos'):
    os.makedirs('photos')

# Список доступных языков
languages = ['en', 'ru', 'de', 'fr', 'it', 'es', 'zh-cn']


# Функция для сохранения фото
@router.message(lambda message: message.photo is not None)
async def save_photo(message: Message):
    # Берем самое качественное фото (последнее в списке)
    photo = message.photo[-1]
    file_name = f"img/{photo.file_id}.jpg"

    # Скачиваем фото
    file = await bot.get_file(photo.file_id)
    await bot.download(file, destination=file_name)

    # Уведомляем пользователя
    await message.reply(f"Ваше фото сохранено как {file_name}")


# Обработка текстового сообщения
@router.message(lambda message: message.text is not None)
async def handle_text(message: Message):
    user_text = message.text

    # Создаём клавиатуру с кнопкой "Сделать голосовое"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Сделать голосовое", callback_data=f"voice:{user_text}"
                )
            ]
        ]
    )

    # Отправляем сообщение с кнопкой
    await message.reply("Нажмите на кнопку, чтобы сгенерировать голосовое сообщение:", reply_markup=keyboard)


# Генерация голосового сообщения с меню выбора языка
@router.callback_query(lambda callback: callback.data.startswith("voice:"))
async def text_to_voice(callback: CallbackQuery):
    user_text = callback.data.split("voice:")[1]
    file_path = f"audio/{callback.id}_random.mp3"

    # Случайный выбор языка
    random_lang = random.choice(languages)
    print(f"Случайно выбранный язык: {random_lang}")

    # Генерация голосового сообщения
    tts = gTTS(user_text, lang=random_lang)
    tts.save(file_path)

    # Отправка голосового сообщения
    voice = FSInputFile(file_path)
    await bot.send_voice(chat_id=callback.message.chat.id, voice=voice)

    # Удаляем файл после отправки (опционально)
    os.remove(file_path)

    # Убираем "часики" на кнопке
    await callback.answer()

    # Пауза перед отправкой меню (имитация ожидания прослушивания)
    await asyncio.sleep(5)

    # Создаем меню с кнопками для выбора языка
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lang.upper(), callback_data=f"select_lang:{lang}:{user_text}") for lang in languages]
        ]
    )

    # Отправляем меню с выбором языка
    await bot.send_message(chat_id=callback.message.chat.id, text="Выберите язык для озвучки:", reply_markup=keyboard)


# Генерация голосового сообщения с выбранным языком
@router.callback_query(lambda callback: callback.data.startswith("select_lang:"))
async def generate_voice_with_selected_lang(callback: CallbackQuery):
    # Извлекаем выбранный язык и текст
    _, selected_lang, user_text = callback.data.split(":", 2)
    file_path = f"audio/{callback.id}_{selected_lang}.mp3"

    print(f"Выбранный язык: {selected_lang}")

    # Генерация голосового сообщения с выбранным языком
    tts = gTTS(user_text, lang=selected_lang)
    tts.save(file_path)

    # Отправка голосового сообщения
    voice = FSInputFile(file_path)
    await bot.send_voice(chat_id=callback.message.chat.id, voice=voice)

    # Удаляем файл (опционально)
    os.remove(file_path)

    # Убираем "часики" на кнопке
    await callback.answer()


# Основная функция для запуска бота
async def main():
    print("Бот запущен...")
    dp.include_router(router)  # Добавляем маршрутизатор в диспетчер
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
