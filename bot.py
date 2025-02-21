from flask import Flask, request
from telegram import Bot
import os
import asyncio

# Загрузка конфигурации из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Токен Telegram-бота
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # Chat ID для отправки сообщений

# Инициализация Flask и Telegram бота
app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Асинхронная функция для отправки сообщения в Telegram
async def send_telegram_message_async(data):
    """
    Формирует и отправляет сообщение в Telegram.
    """
    # Экранируем специальные символы
    def escape_markdown(text):
        if text is None:
            return "N/A"
        return str(text).replace("*", "\\*").replace("_", "\\_").replace("[", "\\[").replace("]", "\\]")

    message = (
        "**🔔 Новая конверсия!**\n\n"  # Жирный текст с эмодзи
        f"📌 Оффер: {escape_markdown(data.get('offer_id'))}\n"
        f"🛠 Подход: {escape_markdown(data.get('sub_id_3'))}\n"
        f"📊 Тип конверсии: {escape_markdown(data.get('goal'))}\n"
        f"⚙️ Статус конверсии: {escape_markdown(data.get('status'))}\n"
        f"🤑 Выплата: {escape_markdown(data.get('revenue'))} {escape_markdown(data.get('currency'))}\n"
        f"🎯 Кампания: {escape_markdown(data.get('sub_id_4'))}\n"
        f"🎯 Адсет: {escape_markdown(data.get('sub_id_5'))}\n"
        f"⏰ Время конверсии: {escape_markdown(data.get('conversion_date'))}"
    )

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='MarkdownV2')

# Эндпоинт для обработки GET и POST запросов
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """
    Обрабатывает GET и POST запросы.
    """
    if request.method == 'POST':
        data = request.json  # Данные из POST-запроса
    else:
        data = request.args  # Данные из GET-запроса

    # Формируем данные для отправки в Telegram
    message_data = {
        'offer_id': data.get('offer_id', 'N/A'),
        'sub_id': data.get('sub_id', 'N/A'),
        'sub_id_2': data.get('sub_id_2', 'N/A'),
        'sub_id_3': data.get('sub_id_3', 'N/A'),
        'sub_id_4': data.get('sub_id_4', 'N/A'),
        'sub_id_5': data.get('sub_id_5', 'N/A'),
        'goal': data.get('goal', 'N/A'),
        'status': data.get('status', 'N/A'),
        'revenue': data.get('revenue', 'N/A'),
        'currency': data.get('currency', 'N/A'),
        'conversion_date': data.get('conversion_date', 'N/A'),
        'click_id': data.get('click_id', 'N/A'),
        'user_id': data.get('user_id', 'N/A')
    }

    # Запускаем асинхронную задачу для отправки сообщения
    asyncio.run(send_telegram_message_async(message_data))
    return 'OK', 200

# Эндпоинт для favicon.ico
@app.route('/favicon.ico')
def favicon():
    return '', 204  # Возвращаем пустой ответ

# Запуск Flask-сервера
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
