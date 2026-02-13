from disnake.ext import commands
import disnake

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="help")
    async def help(self, interaction: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(
            title="📖 Справка по командам",
            description="Список всех доступных команд бота",
            color=disnake.Color.blue()
        )
        
        embed.add_field(
            name="🔨 Модерация",
            value="""
`/ban` - Забанить пользователя
`/unban` - Разбанить пользователя
`/temp_ban` - Временный бан на указанное время
`/kick` - Кикнуть пользователя из сервера
`/clear` - Очистить канал от сообщений
`/say` - Отправить сообщение от имени бота
`/mute` - Отправить участника в Тайм-Аут
            """,
            inline=False
        )
        
        embed.add_field(
            name="👥 Роли",
            value="""
`/give_role` - Выдать роль пользователю
`/remove_role` - Удалить роль у пользователя
            """,
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Развлечение",
            value="`/help` - Показать эту справку\n`/play` - воспроизвести музыку\n`/mafya` - начать игру в мафию",
            inline=False
        )
        
        embed.set_footer(text="Используйте / для просмотра всех команд")
        
        await interaction.response.send_message(embed=embed, ephemeral=False)




def setup(bot):
    bot.add_cog(Help(bot))