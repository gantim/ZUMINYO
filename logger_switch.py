import datetime
import pytz
import os
import discord

class SwitchableLogger:
    def __init__(self, bot, channel_id=1338244641899810907):
        self.bot = bot
        self.channel_id = channel_id
        self.is_enabled = True

    def enable(self):
        self.is_enabled = True
        print("[Логгер] Логирование включено")

    def disable(self):
        self.is_enabled = False
        print("[Логгер] Логирование выключено")

    async def log(self, message):
        if self.is_enabled:
            moscow_tz = pytz.timezone("Europe/Moscow")
            current_time = datetime.datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{current_time} МСК] {message}"

            # Вывод в консоль
            print(formatted_message)

            # Отправка в Discord
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                try:
                    await channel.send(f"```{formatted_message}```")
                except Exception as e:
                    print(f"[Ошибка логирования]: {e}")

if __name__ == "__main__":
    bot = discord.Client(intents=discord.Intents.default())
    logger = SwitchableLogger(bot)
    logger.enable()
