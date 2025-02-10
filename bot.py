import discord
from discord.ext import commands, tasks
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import asyncio
from dotenv import load_dotenv
from countuser import ChannelUpdater
import os

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DISCORD_CHANNEL_ID = 1338223752336375858
TELEGRAM_CHANNEL_ID = -1002276045151
CHANNEL_ID = 1338458279541477418
channel_updater = ChannelUpdater(bot, CHANNEL_ID)

#запуск бота и автоматических функций
@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен!")
    channel_updater.start()

#ping
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

#функция для автоматического апдейта канала с кол-вом участников    
@bot.command()
async def update(ctx):
    await channel_updater.update_channel_name()
    await ctx.send("Название канала обновлено!")    

#отправляет сообщение из тг в дс
async def send_to_discord(message):
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(message)
            
async def telegram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если сообщение пришло в ЛС боту или из группы
    if update.message and update.message.text:
        message_text = update.message.text
    # Если сообщение пришло из Telegram-канала
    elif update.channel_post and update.channel_post.text:
        message_text = update.channel_post.text
    else:
        return  # Игнорируем сообщения без текста (например, стикеры, фото, видео)

    # Проверяем, что сообщение пришло из нужного канала
    if update.effective_chat.id == TELEGRAM_CHANNEL_ID:
        await send_to_discord(message_text)

async def start_telegram_bot():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_handler))
    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, telegram_handler))  # Для каналов

    await application.initialize()

    await application.start()
    print("Telegram-бот запущен!")

    await application.updater.start_polling(drop_pending_updates=True)

async def main():

    telegram_task = asyncio.create_task(start_telegram_bot())
    discord_task = asyncio.create_task(bot.start(DISCORD_TOKEN))

    await asyncio.gather(telegram_task, discord_task)

# Запуск основного цикла событий
if __name__ == "__main__":
    asyncio.run(main())