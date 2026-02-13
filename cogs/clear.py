import disnake
from disnake.ext import commands

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"Удалено {amount} сообщений", delete_after=5)

# ЭТА ФУНКЦИЯ ОБЯЗАТЕЛЬНА
def setup(bot):
    bot.add_cog(Clear(bot))

