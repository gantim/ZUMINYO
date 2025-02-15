from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import aiohttp
import io
import discord
from dotenv import load_dotenv
from logger_switch import SwitchableLogger

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL_ID = int(os.getenv("TELEGRAM_CHANNEL_ID"))
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
logger = SwitchableLogger(None)

async def send_to_discord(bot, logger, message, file_url=None):
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return

    if file_url:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    file_data = await resp.read()
                    filename = file_url.split("/")[-1]

                    file = discord.File(fp=io.BytesIO(file_data), filename=filename)

                    await logger.log(f"Отправка файла {filename} в Discord с сообщением: {message.strip() if message else ''}")
                    await channel.send(content=message if message.strip() else "", file=file)
    else:
        if message.strip():
            await logger.log(f"Отправка сообщения в Discord: {message.strip()}")
            await channel.send(content=message.strip())

async def telegram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot, logger):
    message_text = ""
    file_url = None

    if update.message:
        if update.message.text:
            message_text = update.message.text

        if update.message.photo:
            file = await update.message.photo[-1].get_file()
            file_url = file.file_path
            if update.message.caption: 
                message_text = update.message.caption

        if update.message.video:
            file = await update.message.video.get_file()
            file_url = file.file_path
            if update.message.caption: 
                message_text = update.message.caption

    elif update.channel_post:
        # Аналогично для каналов
        if update.channel_post.text:
            message_text = update.channel_post.text

        if update.channel_post.photo:
            file = await update.channel_post.photo[-1].get_file()
            file_url = file.file_path
            if update.channel_post.caption:
                message_text = update.channel_post.caption

        if update.channel_post.video:
            file = await update.channel_post.video.get_file()
            file_url = file.file_path
            if update.channel_post.caption: 
                message_text = update.channel_post.caption

    await logger.log(f"Получено сообщение из Telegram: {message_text}")
    if "twitch" not in message_text.lower() and update.effective_chat.id == TELEGRAM_CHANNEL_ID:
        await send_to_discord(bot, logger, message_text, file_url)

async def start_telegram_bot(bot, logger):
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(MessageHandler(filters.ALL, lambda update, context: telegram_handler(update, context, bot, logger)))

    await application.initialize()
    await application.start()
    await logger.log("Telegram-бот запущен и начал принимать сообщения!")

    await application.updater.start_polling(drop_pending_updates=True)
