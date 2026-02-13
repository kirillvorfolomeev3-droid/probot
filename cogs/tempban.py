import disnake
from disnake.ext import commands
import asyncio

class Tempban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="temp_ban")
    @commands.has_guild_permissions(ban_members=True)
    async def temp_ban(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.User, duration: int, duration_unit: str, *, reason=None):
        try:
            # Проверка единицы измерения
            if duration_unit not in ["s", "m", "h", "d"]:
                await interaction.response.send_message('❌ Укажите одну из единиц измерения: "s" (секунды), "m" (минуты), "h" (часы), "d" (дни).', ephemeral=True)
                return

            # Переводим время в секунды
            duration_seconds = duration
            if duration_unit == "m":
                duration_seconds *= 60
            elif duration_unit == "h":
                duration_seconds *= 3600
            elif duration_unit == "d":
                duration_seconds *= 86400

            # Баним пользователя
            await interaction.guild.ban(user, reason=reason or "Временный бан")
            unit_names = {"s": "секунд", "m": "минут", "h": "часов", "d": "дней"}
            await interaction.response.send_message(f"✅ Пользователь {user.mention} забанен на {duration} {unit_names.get(duration_unit, 'единиц')}. Причина: {reason or 'Не указана'}", ephemeral=False)

            # Ждем и разбаниваем
            await asyncio.sleep(duration_seconds)

            try:
                # Разбаниваем пользователя по ID
                await interaction.guild.unban(disnake.Object(user.id))
                print(f"✅ Пользователь {user.name} был автоматически разбанен")
            except disnake.NotFound:
                print(f"⚠️ Пользователь {user.name} не найден в списке забаненных")
        except disnake.Forbidden:
            await interaction.response.send_message(f"❌ У меня нет прав для бана {user.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка при бане: {str(e)}", ephemeral=True)

def setup(bot):
    bot.add_cog(Tempban(bot))


