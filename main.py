import asyncio
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.ext._application import Application
from aiohttp import web
from openai import OpenAI

# 🔐 Переменные окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-pPpKsDfa2345d7890xYzvkLmdOpQwKrTft2t3r8t5t1t1")
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "asst_55S2IE1d4Q4ii9VL1BNBw1UC")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7979730053:AAFDIiocR9IsfOj7bimP_ZP8rYgAdS3MCm0")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://telegram-gpt-assistant.onrender.com/")  # Укажи свой Render URL

# Инициализация клиента OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Ответ от GPT-ассистента
async def ask_assistant(user_message):
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status == "completed":
            break
        await asyncio.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    print(f"[LOG] Сообщение: {user_message}")

    try:
        response = await ask_assistant(user_message)
        chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я креативный маркетолог. Напиши мне что-нибудь.")

# Обработка webhook-запросов от Telegram
async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.update_queue.put(update)
    return web.Response()

# Запуск приложения
async def main():
    global application, bot

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()  # type: Application
    bot = application.bot

    # Регистрируем хендлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Aiohttp веб-приложение
    app = web.Application()
    app.router.add_post("/webhook", webhook_handler)
    runner = web.AppRunner(app)

    # Устанавливаем webhook
    await bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print("🤖 Webhook установлен!")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8444)))
    await site.start()

    print(f"✅ Бот слушает на {WEBHOOK_URL}/webhook")

    await application.initialize()
    await application.start()

    # Ожидаем завершения (не polling!)
    await asyncio.Event().wait()
    
if __name__ == "__main__":
    asyncio.run(main())

