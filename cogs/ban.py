from disnake.ext import commands
import disnake

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="ban")
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.User, *, reason=None):
        try:
            await interaction.guild.ban(user, reason=reason)
            await interaction.response.send_message(f"✅ Пользователь {user.mention} забанен. Причина: {reason or 'Не указана'}", ephemeral=False)
        except disnake.Forbidden:
            await interaction.response.send_message(f"❌ У меня нет прав для бана {user.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка при бане: {str(e)}", ephemeral=True)

    @commands.slash_command(name="unban")
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.User):
        try:
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ Пользователь {user.mention} разбанен", ephemeral=False)
        except disnake.NotFound:
            await interaction.response.send_message(f"❌ Пользователь {user.mention} не найден в списке забаненных", ephemeral=True)
        except disnake.Forbidden:
            await interaction.response.send_message(f"❌ У меня нет прав на разбан", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка при разбане: {str(e)}", ephemeral=True)





def setup(bot):
    bot.add_cog(Ban(bot))