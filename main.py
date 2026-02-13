import disnake
from disnake.ext import commands
import json
import os
import logging
from settings_manager import save_settings

# 1. Очищаем экран
os.system('cls' if os.name == 'nt' else 'clear')

# 2. Убираем лишний мусор от библиотеки
logging.getLogger('disnake').setLevel(logging.WARNING)


# 1. Сначала создаем самого бота и его переменные
bot = commands.Bot(command_prefix="!", intents=disnake.Intents.all())
bot.guild_settings = {} # Создаем словарь настроек СРАЗУ

# 2. Потом описываем функцию загрузки
def load_settings():
    if os.path.exists("settings.json"):
        with open("settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for guild_id, settings in data.items():
                bot.guild_settings[int(guild_id)] = settings
            print("[System] Настройки успешно загружены")
    else:
        print("[System] Файл settings.json не найден")

# 3. Теперь ВЫЗЫВАЕМ функцию (после того как она описана и bot создан)
load_settings()

# 3. Загружаем все файлы из папки cogs
for filename in os.listdir("./cogs"):
    # Проверяем, что это файл Python и он не системный (не начинается на __)
    if filename.endswith(".py") and not filename.startswith("__"):
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"[Cogs] Загружен модуль: {filename}")
        except Exception as e:
            print(f"[Error] Не удалось загрузить {filename}: {e}")


# 4. Потом идут события (on_member_join и т.д.)
@bot.event
async def on_member_join(member):
    settings = bot.guild_settings.get(member.guild.id, {})
    # ... твой код автороли и логов ...
    autorole_id = settings.get("autorole_id")
    if autorole_id:
        role = member.guild.get_role(int(autorole_id))
        if role:
            await member.add_roles(role)


    # --- ЛОГИ (Вход) ---
    log_id = settings.get("log_channel_id")
    if log_id:
        channel = bot.get_channel(int(log_id))
        if channel:
            embed = disnake.Embed(
                title="📥 Вход на сервер", 
                description=f"{member.mention} ({member.name}) зашел на сервер.", 
                color=0x8e7dff 
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    
    settings = bot.guild_settings.get(message.guild.id, {})
    log_channel_id = settings.get("log_msg_id")
    
    if log_channel_id:
        channel = bot.get_channel(int(log_channel_id))
        if channel:
            embed = disnake.Embed(title="🗑 Сообщение удалено", color=0xff7675)
            embed.add_field(name="Автор", value=message.author.mention)
            embed.add_field(name="Канал", value=message.channel.mention)
            embed.add_field(name="Содержание", value=message.content or "Пусто/Медиа", inline=False)
            await channel.send(embed=embed)

# Самая последняя строчка в файле (у тебя там был bot.run)
load_settings()
bot.run("MTQ1MjU4OTIyODg3Njg5MDExMg.Gn2pBx.2-HfFzUls3SmM8yYBnQH7UsflYkH1evPEF4ay8")
@bot.event
async def on_member_remove(member):
    # Логика при выходе (кике/бане)
    settings = bot.guild_settings.get(member.guild.id, {})
    log_channel_id = settings.get("log_channel_id")
    
    if log_channel_id:
        channel = member.guild.get_channel(int(log_channel_id))
        if channel:
            embed = disnake.Embed(title="📤 Участник покинул сервер", color=disnake.Color.red())
            embed.add_field(name="Пользователь", value=f"{member.name} ({member.id})")
            await channel.send(embed=embed)

# Исправленный цикл загрузки когов
for filename in os.listdir("./cogs"):
    # Добавляем проверку: загружать только .py и НЕ загружать файлы на __ (типа __init__.py)
    if filename.endswith(".py") and not filename.startswith("__"):
        try:
            bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"[Cogs] Загружен модуль: {filename}")
        except Exception as e:
            print(f"[Error] Не удалось загрузить {filename}: {e}")


@bot.event
async def on_guild_join(guild):
    bot.guild_settings[guild.id] = {
        "prefix": "!",
        "bot_activity_name": "команды"
    }
    save_settings(bot)

# Логирование удаления сообщений
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    settings = bot.guild_settings.get(message.guild.id, {})
    log_channel_id = settings.get("log_msg_id")
    
    if log_channel_id:
        channel = bot.get_channel(int(log_channel_id))
        if channel:
            embed = disnake.Embed(title="🗑 Сообщение удалено", color=0xff7675, timestamp=message.created_at)
            embed.add_field(name="Автор", value=message.author.mention)
            embed.add_field(name="Содержание", value=message.content or "Пусто", inline=False)
            await channel.send(embed=embed)

# Пример команды с проверкой РОЛИ МОДЕРАТОРА
@bot.slash_command(name="kick")
async def kick(inter, member: disnake.Member):
    settings = bot.guild_settings.get(inter.guild.id, {})
    # Берем роль именно для кика из настроек
    allowed_role = settings.get("role_kick") 

    if inter.author.guild_permissions.administrator or (allowed_role and inter.author.get_role(int(allowed_role))):
        await member.kick()
        await inter.send(f"Участник {member.name} кикнут!")
    else:
        await inter.send("У вас нет прав (нужна роль для КИКА из панели)!", ephemeral=True)
    
    
@bot.slash_command(name="ban")
async def ban(inter, member: disnake.Member):
    settings = bot.guild_settings.get(inter.guild.id, {})
    # Берем роль именно для бана
    allowed_role = settings.get("role_ban") 

    if inter.author.guild_permissions.administrator or (allowed_role and inter.author.get_role(int(allowed_role))):
        await member.ban()
        await inter.send(f"Участник {member.name} забанен!")
    else:
        await inter.send("У вас нет прав (нужна роль для БАНА из панели)!", ephemeral=True)

if __name__ == "__main__":
    # Вставь свой токен ниже
    token = "MTQ1MjU4OTIyODg3Njg5MDExMg.Gn2pBx.2-HfFzUls3SmM8yYBnQH7UsflYkH1evPEF4ay8"
    bot.run(token)
