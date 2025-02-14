import discord
from discord.ext import commands
import asyncio
from countuser import ChannelUpdater
from telegram_handler import start_telegram_bot
import os
from dotenv import load_dotenv
import uvicorn
from youtube_webhook import app 

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_USER_ID = int(os.getenv("CHANNEL_USER_ID"))
channel_updater = ChannelUpdater(bot, CHANNEL_USER_ID)

# Запуск бота и автоматических функций
@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен!")
    channel_updater.start()

async def run_webhook():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

# Ping
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# ручное обновление количества участников в канале
@bot.command()
async def update(ctx):
    await channel_updater.update_channel_name()
    await ctx.send("Название канала обновлено!")    

# создание вебхука
@bot.command()
async def create_webhook(ctx, webhook_name="zhume moments"):
    if not ctx.author.guild_permissions.manage_webhooks:
        return await ctx.send("❌ У тебя нет прав на управление вебхуками!")

    webhook = await ctx.channel.create_webhook(name=webhook_name)
    
    await ctx.send(f"✅ Вебхук создан! URL: {webhook.url}")

    print(f"✅ Вебхук создан: {webhook.url}")

#запуск тг бота\дс бота
async def main():
    telegram_task = asyncio.create_task(start_telegram_bot(bot))
    discord_task = asyncio.create_task(bot.start(DISCORD_TOKEN))
    webhook_task = asyncio.create_task(run_webhook())

    await asyncio.gather(telegram_task, discord_task, webhook_task)

if __name__ == "__main__":
    asyncio.run(main())