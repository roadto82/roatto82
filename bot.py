import logging
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
from apscheduler.schedulers.background import BackgroundScheduler
import random
from datetime import time

logging.basicConfig(level=logging.INFO)

# ✅ Твой токен
TOKEN = "7837133555:AAFAQLfxm2SgBuWgedZP_M5fNCd00mvLQoU"

weight_log = {}

recipes = [
    "🍳 Омлет с овощами и курицей — белки, клетчатка, сытно.",
    "🥗 Салат с тунцом, авокадо и оливковым маслом.",
    "🍲 Гречка с овощами и говядиной — простой сбалансированный ужин.",
    "🐟 Запечённый лосось + брокколи на пару + лимон.",
    "🌯 Лаваш с творогом, зеленью и варёным яйцом — быстрый перекус."
]

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я — твой бот-помощник по похудению.\n"
        "/plan — PDF-план\n"
        "/recipe — случайный рецепт\n"
        "/weight — записать текущий вес\n"
        "/history — посмотреть историю веса\n"
        "/help — помощь"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команды:\n/plan\n/recipe\n/weight\n/history")

async def send_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("plan_pokhudeniya_muzhchine.pdf", "rb") as f:
        await update.message.reply_document(InputFile(f), filename="plan_pokhudeniya.pdf")

async def send_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(recipes))

# --- Вес ---
WEIGHT_INPUT = range(1)

async def start_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите ваш текущий вес (в кг):")
    return WEIGHT_INPUT

async def save_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    weight = update.message.text
    if user_id not in weight_log:
        weight_log[user_id] = []
    weight_log[user_id].append(weight)
    await update.message.reply_text(f"Вес {weight} кг записан!")
    return ConversationHandler.END

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    history = weight_log.get(user_id, [])
    if history:
        text = "\n".join([f"{i+1}) {w} кг" for i, w in enumerate(history)])
    else:
        text = "Пока ничего не записано."
    await update.message.reply_text(f"📊 История веса:\n{text}")

# --- Напоминания ---
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in context.application.chat_data.keys():
        await context.bot.send_message(chat_id=chat_id, text="👟 Напоминание: не забудь про движение и правильное питание сегодня!")

def schedule_reminders(application):
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    scheduler.add_job(lambda: application.create_task(send_reminder(application)), trigger='cron', hour=10, minute=0)
    scheduler.start()

# --- Запуск ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("plan", send_plan))
    app.add_handler(CommandHandler("recipe", send_recipe))
    app.add_handler(CommandHandler("history", show_history))

    weight_conv = ConversationHandler(
        entry_points=[CommandHandler("weight", start_weight)],
        states={WEIGHT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_weight)]},
        fallbacks=[]
    )
    app.add_handler(weight_conv)

    schedule_reminders(app)

    print("Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()
