from quart import Quart, request
from telegram import Bot
import os
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
            f"🎯 Цель: {data.get('goal', 'N/A')}\n"
            f"⚙️ Статус: {data.get('status', 'N/A')}\n"
            f"🤑 Выплата: {data.get('revenue', 'N/A')} {data.get('currency', 'N/A')}\n"
            f"🌍 Страна: {data.get('country', 'N/A')}\n"
            f"🆔 ID конверсии: {data.get('id', 'N/A')}\n"
            f"📅 Дата клика: {data.get('click_date', 'N/A')}\n"
            f"📅 Дата конверсии: {data.get('conversion_date', 'N/A')}\n"
            f"🖥 IP: {data.get('ip', 'N/A')}\n"
            f"🎟 Промокод: {data.get('promocode', 'N/A')}\n"
            f"🔗 SubId1: {data.get('sub_id1', 'N/A')}\n"
            f"🔗 SubId2: {data.get('sub_id2', 'N/A')}\n"
            f"🔗 SubId3: {data.get('sub_id3', 'N/A')}\n"
            f"🔗 SubId4: {data.get('sub_id4', 'N/A')}\n"
            f"🔗 SubId5: {data.get('sub_id5', 'N/A')}\n"
            f"🔗 SubId6: {data.get('sub_id6', 'N/A')}\n"
            f"🔗 SubId7: {data.get('sub_id7', 'N/A')}\n"
            f"🔗 SubId8: {data.get('sub_id8', 'N/A')}\n"
            f"🔗 SubId9: {data.get('sub_id9', 'N/A')}\n"
            f"🔗 SubId10: {data.get('sub_id10', 'N/A')}\n"
            f"📝 Custom1: {data.get('custom1', 'N/A')}\n"
            f"📝 Custom2: {data.get('custom2', 'N/A')}\n"
            f"📝 Custom3: {data.get('custom3', 'N/A')}\n"
            f"📝 Custom4: {data.get('custom4', 'N/A')}\n"
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

        # Логирование данных запроса
        logger.info(f"Получены данные: {data}")

        if data is None:
            logger.error("Данные запроса отсутствуют или равны None.")
            return 'Bad Request: Данные отсутствуют', 400

        # Формируем данные для отправки в Telegram
        message_data = {
            'offer_id': data.get('offer_id', 'N/A'),
            'goal': data.get('goal', 'N/A'),
            'status': data.get('status', 'N/A'),
            'revenue': data.get('revenue', 'N/A'),
            'currency': data.get('currency', 'N/A'),
            'country': data.get('country', 'N/A'),
            'id': data.get('id', 'N/A'),
            'click_date': data.get('click_date', 'N/A'),
            'conversion_date': data.get('conversion_date', 'N/A'),
            'ip': data.get('ip', 'N/A'),
            'promocode': data.get('promocode', 'N/A'),
            'sub_id1': data.get('sub_id1', 'N/A'),
            'sub_id2': data.get('sub_id2', 'N/A'),
            'sub_id3': data.get('sub_id3', 'N/A'),
            'sub_id4': data.get('sub_id4', 'N/A'),
            'sub_id5': data.get('sub_id5', 'N/A'),
            'sub_id6': data.get('sub_id6', 'N/A'),
            'sub_id7': data.get('sub_id7', 'N/A'),
            'sub_id8': data.get('sub_id8', 'N/A'),
            'sub_id9': data.get('sub_id9', 'N/A'),
            'sub_id10': data.get('sub_id10', 'N/A'),
            'custom1': data.get('custom1', 'N/A'),
            'custom2': data.get('custom2', 'N/A'),
            'custom3': data.get('custom3', 'N/A'),
            'custom4': data.get('custom4', 'N/A')
        }

        # Логирование сформированных данных
        logger.info(f"Сформированные данные для Telegram: {message_data}")

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
