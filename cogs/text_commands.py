import asyncio
import disnake
from disnake.ext import commands

class TextCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="ping")
    async def ping(self, interaction: disnake.ApplicationCommandInteraction):
        """Простая проверка ответа бота."""
        await interaction.response.send_message("Pong! 🏓")

    @commands.slash_command(name="info")
    async def info(self, interaction: disnake.ApplicationCommandInteraction):
        """Информация о боте."""
        embed = disnake.Embed(title="Info", description="Информация о боте", color=disnake.Color.green())
        embed.add_field(name="User", value=str(self.bot.user), inline=True)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(TextCommands(bot))
