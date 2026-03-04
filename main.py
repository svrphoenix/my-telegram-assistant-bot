from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters, PicklePersistence
from config import config

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello, {update.effective_user.first_name}')

app = ApplicationBuilder().token(config.token).build()

app.add_handler(CommandHandler("start", start))

app.run_polling()

