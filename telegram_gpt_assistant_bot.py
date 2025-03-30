import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# 🔐 Вставь сюда свои ключи
OPENAI_API_KEY = "sk-pPpKsDfa2345d7890xYzvkLmdOpQwKrTft2t3r8t5t1t1"
ASSISTANT_ID = "asst_55S2IE1d4Q4ii9VL1BNBw1UC"
TELEGRAM_TOKEN = "7979730053:AAFDIiocR9IsfOj7bimP_ZP8rYgAdS3MCm0"

# Создаём клиента OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Асинхронная функция для общения с ассистентом
async def ask_assistant(user_message):
    # Создаем новый поток (сессию диалога)
    thread = client.beta.threads.create()

    # Добавляем сообщение от пользователя
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    # Запускаем ассистента
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    # Ждём завершения ответа
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status == "completed":
            break
        await asyncio.sleep(1)

    # Получаем ответ
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    answer = messages.data[0].content[0].text.value
    return answer

# Обработчик сообщений Telegram
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[LOG] Получено сообщение от пользователя: {update.message.text}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": update.message.text}]
    )

    await update.message.reply_text(response.choices[0].message.content)user_message = update.message.text
    await update.message.chat.send_action(action="typing")

    try:
        response = await ask_assistant(user_message)

        # Разбиваем, если слишком длинно
        chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Креативный маркетолог. Напиши мне что-нибудь.")

# Основной запуск
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
