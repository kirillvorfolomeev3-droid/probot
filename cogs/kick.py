import disnake
from disnake.ext import commands

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="kick")
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, interaction: disnake.ApplicationCommandInteraction, member: disnake.Member, *, reason: str = None):
        try:
            if reason is None:
                reason = "Не указана"
            
            await member.kick(reason=reason)
            await interaction.response.send_message(f"✅ Пользователь {member.mention} исключен из сервера. Причина: {reason}", ephemeral=False)
        except disnake.Forbidden:
            await interaction.response.send_message(f"❌ У меня нет прав кикать {member.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка при кике: {str(e)}", ephemeral=True)




def setup(bot):
    bot.add_cog(Kick(bot))