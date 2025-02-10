import discord
from discord.ext import commands, tasks
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import asyncio
from dotenv import load_dotenv
from countuser import ChannelUpdater
from telegram_handler import start_telegram_bot
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
CHANNEL_ID = 1338458279541477418
channel_updater = ChannelUpdater(bot, CHANNEL_ID)

# Запуск бота и автоматических функций
@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен!")
    channel_updater.start()

# Ping
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# ручное обновление количества участников в канале
@bot.command()
async def update(ctx):
    await channel_updater.update_channel_name()
    await ctx.send("Название канала обновлено!")    

#запуск тг бота\дс бота
async def main():
    telegram_task = asyncio.create_task(start_telegram_bot(bot))
    discord_task = asyncio.create_task(bot.start(DISCORD_TOKEN))

    await asyncio.gather(telegram_task, discord_task)

if __name__ == "__main__":
    asyncio.run(main())