from quart import Quart, request
from telegram import Bot
import os
import asyncio
import logging

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Токен Telegram-бота
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # Chat ID для отправки сообщений

# Инициализация Quart и Telegram бота
app = Quart(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Асинхронная функция для отправки сообщения в Telegram
async def send_telegram_message_async(data):
    """
    Формирует и отправляет сообщение в Telegram.
    """
    try:
        message = (
            "<b>🔔 Новая конверсия!</b>\n\n"  # Жирный текст с эмодзи
            f"📌 Оффер: {data.get('offer_id', 'N/A')}\n"
            f"🛠 Подход: {data.get('sub_id3', 'N/A')}\n"
            f"📊 Тип конверсии: {data.get('goal', 'N/A')}\n"
            f"⚙️ Статус конверсии: {data.get('status', 'N/A')}\n"
            f"🤑 Выплата: {data.get('revenue', 'N/A')} {data.get('currency', 'N/A')}\n"
            f"🎯 Кампания: {data.get('sub_id4', 'N/A')}\n"
            f"🎯 Адсет: {data.get('sub_id5', 'N/A')}\n"
            f"⏰ Время конверсии: {data.get('conversion_date', 'N/A')}"
        )
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
        logger.info("Сообщение успешно отправлено в Telegram.")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")

# Эндпоинт для обработки GET и POST запросов
@app.route('/webhook', methods=['GET', 'POST'])
async def webhook():
    """
    Обрабатывает GET и POST запросы.
    """
    try:
        if request.method == 'POST':
            data = await request.json  # Данные из POST-запроса
        else:
            data = request.args  # Данные из GET-запроса

        # Формируем данные для отправки в Telegram
        message_data = {
            'offer_id': data.get('offer_id', 'N/A'),
            'sub_id_3': data.get('sub_id3', 'N/A'),
            'goal': data.get('goal', 'N/A'),
            'status': data.get('status', 'N/A'),
            'revenue': data.get('revenue', 'N/A'),
            'currency': data.get('currency', 'N/A'),
            'sub_id_4': data.get('sub_id4', 'N/A'),
            'sub_id_5': data.get('sub_id5', 'N/A'),
            'conversion_date': data.get('conversion_date', 'N/A')
        }

        # Запускаем асинхронную задачу
        await send_telegram_message_async(message_data)
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        return 'Internal Server Error', 500

# Эндпоинт для favicon.ico
@app.route('/favicon.ico')
async def favicon():
    return '', 204  # Возвращаем пустой ответ

# Запуск Quart-сервера
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Используем порт из переменной окружения или 5000 по умолчанию
    app.run(host='0.0.0.0', port=port)
