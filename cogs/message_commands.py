import asyncio
import disnake
from disnake.ext import commands

class MessageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        await ctx.send("я работаю и так отстань! 🏓")
def setup(bot):
    bot.add_cog(MessageCommands(bot)) # Вместо ВашеИмяКласса напиши имя класса из этого файла

    

