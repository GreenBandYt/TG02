from config import TOKEN

import os
import random
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from gtts import gTTS
from deep_translator import GoogleTranslator

# Укажите ваш токен
BOT_TOKEN = TOKEN

# Инициализация объектов
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Создаем папки для сохранения файлов
if not os.path.exists('audio'):
    os.makedirs('audio')
if not os.path.exists('img'):
    os.makedirs('img')

# Список доступных языков
languages = ['en', 'ru', 'de', 'fr', 'it', 'es', 'zh-cn']

# Хранилище текстов
text_storage = {}


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
    await message.reply(f"Ваше фото сохранено в папке img как {file_name}")


# Обработка текстового сообщения
@router.message(lambda message: message.text is not None)
async def handle_text(message: Message):
    user_text = message.text

    # Сохраняем текст в хранилище с идентификатором сообщения
    text_storage[message.message_id] = user_text

    # Создаём клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Сделать голосовое", callback_data=f"voice:{message.message_id}"
                ),
                InlineKeyboardButton(
                    text="Перевести текст", callback_data=f"translate:{message.message_id}"
                )
            ]
        ]
    )

    # Отправляем сообщение с кнопками
    await message.reply("Выберите действие:", reply_markup=keyboard)


# Генерация голосового сообщения с меню выбора языка
@router.callback_query(lambda callback: callback.data.startswith("voice:"))
async def text_to_voice(callback: CallbackQuery):
    # Извлекаем идентификатор сообщения
    message_id = int(callback.data.split("voice:")[1])
    user_text = text_storage.get(message_id, "Текст не найден.")

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
            [InlineKeyboardButton(text=lang.upper(), callback_data=f"select_lang:{lang}:{message_id}") for lang in languages]
        ]
    )

    # Отправляем меню с выбором языка
    await bot.send_message(chat_id=callback.message.chat.id, text="Выберите язык для озвучки:", reply_markup=keyboard)


# Генерация голосового сообщения с выбранным языком
@router.callback_query(lambda callback: callback.data.startswith("select_lang:"))
async def generate_voice_with_selected_lang(callback: CallbackQuery):
    # Извлекаем выбранный язык и идентификатор текста
    _, selected_lang, message_id = callback.data.split(":", 2)
    message_id = int(message_id)
    user_text = text_storage.get(message_id, "Текст не найден.")

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


# Функция для перевода текста
@router.callback_query(lambda callback: callback.data.startswith("translate:"))
async def translate_text(callback: CallbackQuery):
    # Извлекаем идентификатор сообщения
    message_id = int(callback.data.split("translate:")[1])
    user_text = text_storage.get(message_id, "Текст не найден.")

    # Перевод текста на английский
    translated = GoogleTranslator(source='auto', target='en').translate(user_text)

    # Отправляем перевод пользователю
    await callback.message.reply(f"Перевод текста:\n{translated}")

    # Убираем "часики" на кнопке
    await callback.answer()


# Основная функция для запуска бота
async def main():
    print("Бот запущен...")
    dp.include_router(router)  # Добавляем маршрутизатор в диспетчер
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
