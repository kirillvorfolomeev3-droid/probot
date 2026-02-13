import disnake
from disnake.ext import commands
import datetime
import re

# Регулярное выражение для поиска чисел и букв (s, m, h, d)
time_regex = re.compile(r"(\d+)([smhd])?")

def parse_time(time_str: str):
    matches = time_regex.fullmatch(time_str.lower())
    if not matches:
        return None
    
    amount, unit = matches.groups()
    amount = int(amount)
    
    if unit == "s": # секунды
        return datetime.timedelta(seconds=amount)
    elif unit == "m" or unit is None: # минуты (по умолчанию)
        return datetime.timedelta(minutes=amount)
    elif unit == "h": # часы
        return datetime.timedelta(hours=amount)
    elif unit == "d": # дни
        return datetime.timedelta(days=amount)
    return None

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def apply_mute(self, author, member, duration_str, reason):
        if member == author:
            return "Вы не можете замутить самого себя!"
        
        if member.top_role >= author.top_role and author != author.guild.owner:
            return "Ваша роль ниже или равна роли этого участника!"

        duration = parse_time(duration_str)
        if duration is None:
            return "Неверный формат времени! Используйте: 10s, 5m, 1h, 1d."

        try:
            await member.timeout(duration=duration, reason=reason)
            return duration
        except disnake.Forbidden:
            return "У меня нет прав для мута этого пользователя."
        except Exception as e:
            return f"Ошибка: {e}"

    # Команда !mute @user 2m причина
    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def prefix_mute(self, ctx, member: disnake.Member, time: str, *, reason="Нарушение правил"):
        result = await self.apply_mute(ctx.author, member, time, reason)
        
        if isinstance(result, datetime.timedelta):
            await ctx.send(f"✅ {member.mention} был ограничен в общении на **{time}**. Причина: {reason}")
        else:
            await ctx.send(f"❌ {result}")

    # Слэш-команда /mute
    @commands.slash_command(name="mute", description="Замутить участника")
    @commands.has_permissions(moderate_members=True)
    async def slash_mute(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, time: str, reason: str = "Нарушение правил"):
        result = await self.apply_mute(inter.author, member, time, reason)
        
        if isinstance(result, datetime.timedelta):
            await inter.response.send_message(f"✅ {member.mention} замучен на **{time}**. Причина: {reason}")
        else:
            await inter.response.send_message(f"❌ {result}", ephemeral=True)

def setup(bot):
    bot.add_cog(Moderation(bot))


