import disnake
from disnake.ext import commands

class SayCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ОБЫЧНАЯ КОМАНДА (!say текст) ---
    @commands.command(name="say", help="Отправить сообщение от имени бота")
    @commands.has_permissions(manage_messages=True) # Только для модераторов
    async def prefix_say(self, ctx, *, message: str):
        # Удаляем сообщение пользователя, чтобы "сказал" только бот
        try:
            await ctx.message.delete()
        except disnake.Forbidden:
            pass # Если нет прав на удаление сообщений
        
        await ctx.send(message)

    # --- СЛЭШ-КОМАНДА (/say текст) ---
    @commands.slash_command(name="say", description="Отправить сообщение от имени бота")
    @commands.has_permissions(manage_messages=True)
    async def slash_say(self, inter: disnake.ApplicationCommandInteraction, message: str):
        # Слэш-команды требуют ответа. Мы отправим сообщение в канал,
        # а пользователю ответим невидимым (ephemeral) подтверждением.
        await inter.channel.send(message)
        await inter.response.send_message("Сообщение отправлено!", ephemeral=True)

    # Обработка ошибки, если у пользователя нет прав
    @prefix_say.error
    @slash_say.error
    async def say_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ У вас недостаточно прав для использования этой команды!", delete_after=5)

def setup(bot):
    bot.add_cog(SayCommand(bot))