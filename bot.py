from flask import Flask, request
from telegram import Bot
import os

# Загрузка конфигурации из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Токен Telegram-бота
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # Chat ID для отправки сообщений

# Инициализация Flask и Telegram бота
app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Функция для отправки сообщения в Telegram
def send_telegram_message(data):
    """
    Формирует и отправляет сообщение в Telegram.
    """
    message = (
        f"📌 Оффер: {data.get('offer_id', 'N/A')}\n"
        f"🛠 Подход: {data.get('sub_id', 'N/A')}\n"
        f"📊 Тип конверсии: {data.get('goal', 'N/A')}\n"
        f"⚙️ Статус конверсии: {data.get('status', 'N/A')}\n"
        f"🤑 Выплата: {data.get('revenue', 'N/A')} {data.get('currency', 'N/A')}\n"
        f"🎯 Кампания: {data.get('sub_id_4', 'N/A')}\n"
        f"🎯 Адсет: {data.get('sub_id_5', 'N/A')}\n"
        f"⏰ Время конверсии: {data.get('conversion_date', 'N/A')}"
    )
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# Эндпоинт для обработки query-параметров
@app.route('/webhook', methods=['GET'])
def webhook():
    """
    Обрабатывает GET-запросы с query-параметрами.
    """
    # Получаем query-параметры
    sub_id = request.args.get('sub_id')
    offer_id = request.args.get('offer_id')

    # Формируем данные для отправки в Telegram
    data = {
        'sub_id': sub_id,
        'offer_id': offer_id,
        'goal': request.args.get('goal', 'N/A'),
        'status': request.args.get('status', 'N/A'),
        'revenue': request.args.get('revenue', 'N/A'),
        'currency': request.args.get('currency', 'N/A'),
        'sub_id_4': request.args.get('sub_id_4', 'N/A'),
        'sub_id_5': request.args.get('sub_id_5', 'N/A'),
        'conversion_date': request.args.get('conversion_date', 'N/A')
    }

    # Отправляем данные в Telegram
    send_telegram_message(data)
    return 'OK', 200

# Запуск Flask-сервера
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)