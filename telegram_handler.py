from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = -1002276045151
DISCORD_CHANNEL_ID = 1338223752336375858

async def send_to_discord(bot, message):
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(message)

async def telegram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot):
    if update.message and update.message.text:
        message_text = update.message.text
    elif update.channel_post and update.channel_post.text:
        message_text = update.channel_post.text
    else:
        return

    if update.effective_chat.id == TELEGRAM_CHANNEL_ID:
        await send_to_discord(bot, message_text)

async def start_telegram_bot(bot):
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: telegram_handler(update, context, bot)))
    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, lambda update, context: telegram_handler(update, context, bot)))

    await application.initialize()
    await application.start()
    print("Telegram-бот запущен!")

    await application.updater.start_polling(drop_pending_updates=True)
