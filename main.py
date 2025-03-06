import logging
from config import TOKEN
import os
import random
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from gtts import gTTS, gTTSError
from deep_translator import GoogleTranslator
from time import sleep

# Настроим логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
languages = ['en', 'ru', 'de', 'fr', 'it', 'es', 'fi']

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
    await file.download(destination=file_name)

    logger.info(f"Фото сохранено как {file_name}")
    await message.reply(f"Ваше фото сохранено в папке img как {file_name}")


# Обработка текстового сообщения
@router.message(lambda message: message.text is not None)
async def handle_text(message: Message):
    user_text = message.text

    logger.info(f"Получено текстовое сообщение: {user_text}")

    # Сохраняем текст в хранилище с идентификатором сообщения
    text_storage[message.message_id] = user_text

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="Сделать голосовое", callback_data=f"voice:{message.message_id}"
            ),
            InlineKeyboardButton(
                text="Перевести текст", callback_data=f"translate:{message.message_id}"
            )
        ]]
    )

    logger.info("Отправлены кнопки для выбора действия")
    # Отправляем сообщение с кнопками
    await message.reply("Выберите действие:", reply_markup=keyboard)


# Генерация голосового сообщения с меню выбора языка
@router.callback_query(lambda callback: callback.data.startswith("voice:"))
async def text_to_voice(callback: CallbackQuery):
    # Извлекаем идентификатор сообщения
    message_id = int(callback.data.split("voice:")[1])
    user_text = text_storage.get(message_id, "Текст не найден.")

    logger.info(f"Генерация голосового сообщения для текста: {user_text}")

    file_path = f"audio/{callback.id}_random.mp3"

    # Случайный выбор языка
    random_lang = random.choice(languages)
    logger.info(f"Случайно выбранный язык: {random_lang}")

    # Генерация голосового сообщения с повторными попытками
    try:
        await generate_voice_with_retries(user_text, random_lang, file_path)
    except gTTSError as e:
        logger.error(f"Ошибка при генерации речи: {e}")
        await callback.message.reply(f"Ошибка при генерации речи: {e}")
        return

    # Отправка голосового сообщения
    voice = FSInputFile(file_path)
    await bot.send_voice(chat_id=callback.message.chat.id, voice=voice)

    # Уведомляем о выбранном языке
    logger.info(f"Голосовое сообщение отправлено с акцентом {random_lang.upper()} языка")
    await bot.send_message(chat_id=callback.message.chat.id, text=f"Озвучено с акцентом {random_lang.upper()} языка:")

    # Удаляем файл после отправки
    os.remove(file_path)

    # Создаем меню с кнопками выбора языка
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=lang.upper(), callback_data=f"select_lang:{lang}:{message_id}") for lang in languages
        ]]
    )

    # Отправляем меню с выбором языка
    logger.info("Отправлены кнопки для выбора языка озвучки")
    await bot.send_message(chat_id=callback.message.chat.id, text="Выберите язык для озвучки:", reply_markup=keyboard)

    # Убираем "часики" на кнопке
    await callback.answer()


# Генерация голосового сообщения с выбранным языком
@router.callback_query(lambda callback: callback.data.startswith("select_lang:"))
async def generate_voice_with_selected_lang(callback: CallbackQuery):
    # Извлекаем выбранный язык и идентификатор текста
    _, selected_lang, message_id = callback.data.split(":", 2)
    message_id = int(message_id)
    user_text = text_storage.get(message_id, "Текст не найден.")

    file_path = f"audio/{callback.id}_{selected_lang}.mp3"

    logger.info(f"Генерация голосового сообщения для текста на языке: {selected_lang}")

    # Генерация голосового сообщения с выбранным языком
    try:
        await generate_voice_with_retries(user_text, selected_lang, file_path)
    except gTTSError as e:
        logger.error(f"Ошибка при генерации речи: {e}")
        await callback.message.reply(f"Ошибка при генерации речи: {e}")
        return

    # Отправка голосового сообщения
    voice = FSInputFile(file_path)
    await bot.send_voice(chat_id=callback.message.chat.id, voice=voice)

    # Уведомляем о выбранном языке
    logger.info(f"Голосовое сообщение отправлено с акцентом {selected_lang.upper()} языка")
    await bot.send_message(chat_id=callback.message.chat.id, text=f"Озвучено с акцентом {selected_lang.upper()} языка:")

    # Удаляем файл после отправки
    os.remove(file_path)

    # Убираем "часики" на кнопке
    await callback.answer()


# Функция для генерации голосового сообщения с повторными попытками
async def generate_voice_with_retries(user_text, lang, file_path, retries=3):
    for attempt in range(retries):
        try:
            tts = gTTS(user_text, lang=lang)
            tts.save(file_path)
            logger.info(f"Голосовое сообщение сохранено в файл: {file_path}")
            return file_path
        except gTTSError as e:
            logger.error(f"Ошибка при генерации речи (попытка {attempt + 1}): {e}")
            if attempt < retries - 1:
                sleep(2)  # Пауза перед повторной попыткой
            else:
                raise Exception("Не удалось подключиться к Google TTS после нескольких попыток.")


# Обработка кнопки "Перевести текст" — выбор языка перевода
@router.callback_query(lambda callback: callback.data.startswith("translate:"))
async def choose_translation_language(callback: CallbackQuery):
    # Извлекаем идентификатор сообщения
    message_id = int(callback.data.split("translate:")[1])
    user_text = text_storage.get(message_id, "Текст не найден.")

    # Сохраняем текст в хранилище (опционально, для дальнейшего использования)
    text_storage[callback.id] = user_text

    # Создаем меню с кнопками выбора языка
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=lang.upper(), callback_data=f"translate_to:{lang}:{callback.id}") for lang in languages
        ]]
    )

    # Отправляем меню с языками
    logger.info(f"Отправлено меню с языками для перевода текста: {user_text}")
    await bot.send_message(chat_id=callback.message.chat.id, text="Выберите язык перевода:", reply_markup=keyboard)
    await callback.answer()  # Убираем "часики" на кнопке


# Выполнение перевода на выбранный язык
@router.callback_query(lambda callback: callback.data.startswith("translate_to:"))
async def translate_text(callback: CallbackQuery):
    # Извлекаем выбранный язык и идентификатор текста
    _, target_lang, text_id = callback.data.split(":", 2)
    user_text = text_storage.get(text_id, "Текст не найден.")

    # Выполняем перевод
    try:
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(user_text)
        logger.info(f"Перевод выполнен на {target_lang.upper()}: {translated_text}")
    except Exception as e:
        translated_text = f"Ошибка перевода: {e}"
        logger.error(f"Ошибка при переводе текста: {e}")

    # Отправляем переведённый текст
    await bot.send_message(chat_id=callback.message.chat.id, text=f"Перевод на {target_lang.upper()}:\n{translated_text}")
    await callback.answer()  # Убираем "часики" на кнопке


# Основная функция для запуска бота
async def main():
    logger.info("Бот запущен...")
    dp.include_router(router)  # Добавляем маршрутизатор в диспетчер
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
