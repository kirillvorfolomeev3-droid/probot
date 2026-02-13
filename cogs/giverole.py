import disnake
from disnake.ext import commands

class GiveRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="give_role")
    @commands.has_guild_permissions(manage_roles=True)
    async def give_role(self, interaction: disnake.ApplicationCommandInteraction, member: disnake.Member, role: disnake.Role):
        try:
            if role.position >= interaction.author.top_role.position:
                await interaction.response.send_message(f"❌ Вы не можете выдать роль {role.mention}, т.к. она равна или выше вашей роли", ephemeral=True)
                return
            
            await member.add_roles(role)
            await interaction.response.send_message(f"✅ Роль {role.mention} успешно выдана пользователю {member.mention}", ephemeral=False)
        except disnake.Forbidden:
            await interaction.response.send_message(f"❌ У меня нет прав выдать эту роль", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)

    @commands.slash_command(name="remove_role")
    @commands.has_guild_permissions(manage_roles=True)
    async def remove_role(self, interaction: disnake.ApplicationCommandInteraction, member: disnake.Member, role: disnake.Role):
        try:
            if role.position >= interaction.author.top_role.position:
                await interaction.response.send_message(f"❌ Вы не можете удалить роль {role.mention}", ephemeral=True)
                return
            
            await member.remove_roles(role)
            await interaction.response.send_message(f"✅ Роль {role.mention} удалена у пользователя {member.mention}", ephemeral=False)
        except disnake.Forbidden:
            await interaction.response.send_message(f"❌ У меня нет прав удалить эту роль", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)

def setup(bot):
    bot.add_cog(GiveRole(bot))
