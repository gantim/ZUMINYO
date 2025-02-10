import discord
from discord.ext import tasks

class ChannelUpdater:
    def __init__(self, bot, channel_id):
        self.bot = bot
        self.channel_id = channel_id

    @tasks.loop(minutes=60)
    async def update_channel_name(self):
        guild = discord.utils.get(self.bot.guilds)
        if guild:
            total_members = guild.member_count
            online_members = sum(1 for m in guild.members if m.status == discord.Status.online)
            offline_members = total_members - online_members

            new_name = f"Участников: {total_members}"

            channel = discord.utils.get(guild.channels, id=self.channel_id)
            if channel and isinstance(channel, discord.VoiceChannel):
                await channel.edit(name=new_name)
                # print(f"Название канала обновлено на: {new_name}")

    def start(self):
        self.update_channel_name.start()

    def stop(self):
        self.update_channel_name.cancel()
