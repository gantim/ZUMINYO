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
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))
CHANNEL_USER_ID = int(os.getenv("CHANNEL_USER_ID"))
channel_updater = ChannelUpdater(bot, CHANNEL_USER_ID)
MESSAGE_ID_FILE = "roles_message.txt"

REACTION_ROLE_MAP = {
    1339932890515116103: "CSGO",
    1339932919581376645: "Apex", 
    1339934851817668649: "Dota",  
    1339935764967849994: "Valorant",  
    1339936065150128310: "Fortnite"
}

# Запуск автоматических функций
@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен!")
    channel_updater.start()

    guild = bot.get_guild(GUILD_ID)
    message_id = await load_message_id()

    if message_id:
        print(f"Загружено сообщение с ID: {message_id} для отслеживания реакций")
    else:
        await send_roles_message(guild)

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
    
async def save_message_id(message):
    with open(MESSAGE_ID_FILE, "w") as f:
        f.write(str(message.id))

async def load_message_id():
    if os.path.exists(MESSAGE_ID_FILE):
        with open(MESSAGE_ID_FILE, "r") as f:
            return int(f.read())
    return None

# ручное создание выдачи ролей
@bot.command()
async def roles(ctx):
    guild = ctx.guild
    await send_roles_message(guild)
    await ctx.message.delete()

async def send_roles_message(guild):
    channel = discord.utils.get(guild.text_channels, name="🍥〡роли")
    if not channel:
        print("❌ Канал для ролей не найден!")
        return

    message_text = "Выберите реакцию, чтобы получить роль по любимой игре:\n"
    for emoji_id, role_name in REACTION_ROLE_MAP.items():
        emoji = discord.utils.get(guild.emojis, id=emoji_id)
        if emoji:
            message_text += f"{emoji} - {role_name}\n"

    sent_message = await channel.send(message_text)

    # Сохраняем ID сообщения
    await save_message_id(sent_message)

    # Добавляем реакции
    for emoji_id in REACTION_ROLE_MAP.keys():
        emoji = discord.utils.get(guild.emojis, id=emoji_id)
        if emoji:
            await sent_message.add_reaction(emoji)

    print(f"📌 Новое сообщение с реакциями отправлено! ID: {sent_message.id}")

# Используем RAW события, чтобы отслеживать реакции после перезапуска!
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    emoji_id = payload.emoji.id

    if emoji_id in REACTION_ROLE_MAP:
        role_name = REACTION_ROLE_MAP[emoji_id]
        role = discord.utils.get(guild.roles, name=role_name)

        if role and member:
            await member.add_roles(role)
            print(f"✅ Роль {role_name} добавлена пользователю {member.name}")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    emoji_id = payload.emoji.id

    if emoji_id in REACTION_ROLE_MAP:
        role_name = REACTION_ROLE_MAP[emoji_id]
        role = discord.utils.get(guild.roles, name=role_name)

        if role and member:
            await member.remove_roles(role)
            print(f"❌ Роль {role_name} убрана у пользователя {member.name}")

async def main():
    telegram_task = asyncio.create_task(start_telegram_bot(bot))
    discord_task = asyncio.create_task(bot.start(DISCORD_TOKEN))
    webhook_task = asyncio.create_task(run_webhook())

    await asyncio.gather(telegram_task, discord_task, webhook_task)

if __name__ == "__main__":
    asyncio.run(main())