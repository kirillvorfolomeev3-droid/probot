import asyncio
import disnake
from disnake.ext import commands
import time
import os
import logging

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- НАСТРОЙКИ ---
YTDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'socket_timeout': 15,  # Увеличим таймаут
    'source_address': '0.0.0.0', # Принудительно IPv4 (помогает против ошибок 10054)
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'default_search': 'scsearch', # ***ВЕРНУЛИСЬ НА SOUNDCLOUD ДЛЯ СТАБИЛЬНОСТИ***
    'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    'noplaylist': True,
    'extractor_retries': 3, # Добавляем повторные попытки для yt-dlp
}

FFMPEG_OPTIONS = {
    'options': '-vn',
    # 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', # Убрал, может мешать
}

# --- ПОМОЩНИКИ ДЛЯ ОТВЕТОВ ---
async def _send_dynamic_response(interaction_obj, content: str, ephemeral: bool = False):
    """Отправляет ответ, адаптированный для Context или ApplicationCommandInteraction."""
    if isinstance(interaction_obj, disnake.ApplicationCommandInteraction):
        if interaction_obj.response.is_done():
            await interaction_obj.followup.send(content, ephemeral=ephemeral)
        else:
            await interaction_obj.edit_original_response(content=content)
    elif isinstance(interaction_obj, commands.Context):
        await interaction_obj.send(content)

# --- КНОПКИ УПРАВЛЕНИЯ ---
class MusicControlView(disnake.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player = player

    @disnake.ui.button(label="-15s", style=disnake.ButtonStyle.secondary, emoji="⏪")
    async def rewind(self, button, inter):
        await self.player.seek(-15)
        await inter.response.send_message("⏪ -15 секунд", ephemeral=True)

    @disnake.ui.button(label="⏯️", style=disnake.ButtonStyle.primary)
    async def toggle_pause(self, button, inter):
        if self.player.voice and self.player.voice.is_paused():
            self.player.voice.resume()
            await inter.response.send_message("▶️ Продолжаем", ephemeral=True)
        elif self.player.voice and self.player.voice.is_playing():
            self.player.voice.pause()
            await inter.response.send_message("⏸️ Пауза", ephemeral=True)
        else:
            await inter.response.send_message("🤷 Ничего не играет", ephemeral=True)

    @disnake.ui.button(label="⏭️", style=disnake.ButtonStyle.success)
    async def skip(self, button, inter):
        if self.player.voice and (self.player.voice.is_playing() or self.player.voice.is_paused()):
            self.player.voice.stop()
            await inter.response.send_message("⏭️ Пропущено", ephemeral=True)
        else:
            await inter.response.send_message("🤷 Ничего не играет", ephemeral=True)

    @disnake.ui.button(label="+15s", style=disnake.ButtonStyle.secondary, emoji="⏩")
    async def fast_forward(self, button, inter):
        await self.player.seek(15)
        await inter.response.send_message("⏩ +15 секунд", ephemeral=True)

    @disnake.ui.button(label="⏹️", style=disnake.ButtonStyle.danger)
    async def stop_bot(self, button, inter):
        await self.player.stop()
        await inter.response.send_message("⏹️ Остановлено", ephemeral=True)

# --- ЛОГИКА ПЛЕЕРА ---
class GuildPlayer:
    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild
        self.queue = asyncio.Queue()
        self.play_next = asyncio.Event()
        self.current = None
        self.voice = None
        self.position = 0
        self.start_time = 0
        self.loop_task = None
        self.ytdl = yt_dlp.YoutubeDL(YTDL_OPTS)

    async def seek(self, seconds):
        if not self.voice or not self.current: return
        elapsed = time.time() - self.start_time
        self.position = max(0, self.position + elapsed + seconds)
        if self.voice.is_playing() or self.voice.is_paused():
            self.voice.stop()

    async def player_loop(self):
        while True:
            self.play_next.clear()
            if self.position == 0:
                try:
                    self.current = await asyncio.wait_for(self.queue.get(), timeout=300)
                    logger.info(f"Получен трек из очереди: {self.current.get('title', 'Неизвестно')}")
                except asyncio.TimeoutError:
                    logger.info(f"Очередь пуста в {self.guild.name}. Отключение бота.")
                    await self.stop()
                    return
            
            try:
                loop = asyncio.get_event_loop()
                # URL для yt-dlp: если это не ссылка, используем default_search (SoundCloud)
                query_for_ytdl = self.current['url']
                
                logger.info(f"yt-dlp: Извлечение информации для: {query_for_ytdl}")
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(query_for_ytdl, download=False))
                
                if not data:
                    logger.error(f"yt-dlp не вернул данные для {query_for_ytdl}")
                    self.current = None
                    continue

                if 'entries' in data and data['entries']:
                    data = data['entries'][0]
                elif 'entries' in data and not data['entries']:
                    logger.warning(f"yt-dlp вернул пустой список записей для {query_for_ytdl}")
                    self.current = None
                    continue
                
                url = data.get('url')
                if not url:
                    logger.error(f"yt-dlp не смог получить URL потока для {self.current.get('title', 'Неизвестно')}. Данные: {data.keys()}")
                    self.current = None
                    continue

                logger.info(f"FFmpeg: Начало воспроизведения {self.current.get('title', 'Неизвестно')} с URL: {url[:50]}...")
                
                ffmpeg_opts = {
                    'before_options': f'-ss {int(self.position)}', # Снова упрощаем
                    **FFMPEG_OPTIONS, # Добавляем остальные опции из FFMPEG_OPTIONS
                }
                
                if not self.voice or not self.voice.is_connected():
                    logger.warning(f"Бот не подключен к голосовому каналу {self.guild.name}. Остановка воспроизведения.")
                    await self.stop()
                    return
                    
                source = disnake.FFmpegPCMAudio(url, **ffmpeg_opts)
                # Обертка для регулировки громкости (иногда помогает "протолкнуть" звук)
                source = disnake.PCMVolumeTransformer(source, volume=0.8)

                self.start_time = time.time()
                
                self.voice.play(source, after=lambda e: self.bot.loop.call_soon_threadsafe(self.play_next.set))
                
                if self.position == 0:
                    await self.voice.channel.send(f"🎶 Сейчас играет: **{self.current.get('title', 'Трек')}**", view=MusicControlView(self))
                
                await self.play_next.wait()
                
                logger.info(f"Воспроизведение трека {self.current.get('title', 'Неизвестно')} завершено.")
                self.position = 0
                self.current = None
                
            except Exception as e:
                logger.error(f"Ошибка в цикле player_loop для {self.current.get('title', 'Неизвестно')}: {type(e).__name__} - {e}")
                self.position = 0
                await asyncio.sleep(2)
                continue

    async def add(self, query: str, inter_obj):
        """Добавляет трек в очередь."""
        if not self.ytdl:
            await _send_dynamic_response(inter_obj, "❌ Модуль `yt-dlp` не установлен. Установите `pip install yt-dlp`.", ephemeral=True)
            return None
            
        # Используем default_search (SoundCloud) для текстовых запросов, иначе - как есть
        search_query = query if query.startswith("http") else query 
            
        try:
            loop = asyncio.get_event_loop()
            logger.info(f"yt-dlp: Поиск информации для добавления: {search_query}")
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(search_query, download=False))
            
            if not data:
                logger.warning(f"yt-dlp не вернул данные при добавлении для запроса: {search_query}")
                await _send_dynamic_response(inter_obj, "❌ Трек не найден.", ephemeral=True)
                return None
            
            if 'entries' in data:
                if not data['entries']:
                    logger.warning(f"yt-dlp вернул пустой список записей при добавлении для запроса: {search_query}")
                    await _send_dynamic_response(inter_obj, "❌ Трек не найден.", ephemeral=True)
                    return None
                data = data['entries'][0]
            
            entry = {
                'url': data.get('webpage_url') or data.get('url'),
                'title': data.get('title', 'Без названия'),
                'duration': data.get('duration')
            }
            if not entry['url'] or not entry['title']:
                logger.error(f"Не удалось получить полный URL или название трека из данных: {data}")
                await _send_dynamic_response(inter_obj, "❌ Не удалось получить полную информацию о треке.", ephemeral=True)
                return None
                
            await self.queue.put(entry)
            logger.info(f"Трек добавлен в очередь: {entry['title']}")
            return entry
            
        except yt_dlp.DownloadError as e:
            logger.error(f"Ошибка yt-dlp при добавлении трека: {e}. Запрос: {search_query}")
            await _send_dynamic_response(inter_obj, f"❌ Ошибка загрузки: {e}\n*(Для VK убедитесь в наличии `cookies.txt`)*", ephemeral=True)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения информации о треке (add): {type(e).__name__} - {e}. Запрос: {search_query}")
            await _send_dynamic_response(inter_obj, f"❌ Произошла ошибка: {e}", ephemeral=True)
            return None

    async def start_loop(self):
        """Запускает или перезапускает цикл воспроизведения."""
        if self.loop_task is None or self.loop_task.done():
            self.loop_task = asyncio.create_task(self.player_loop())

    async def stop(self):
        """Останавливает воспроизведение и отключает бота."""
        self.queue = asyncio.Queue()
        if self.voice and self.voice.is_connected():
            await self.voice.disconnect()
        if self.loop_task:
            self.loop_task.cancel()
            self.loop_task = None
        self.current = None
        self.position = 0

# --- КОМАНДЫ ---
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    def get_player(self, guild):
        if guild.id not in self.players:
            self.players[guild.id] = GuildPlayer(self.bot, guild)
        return self.players[guild.id]

    async def connect_voice(self, inter_obj):
        """Подключает бота к голосовому каналу пользователя."""
        if not inter_obj.author.voice or not inter_obj.author.voice.channel:
            await _send_dynamic_response(inter_obj, "❌ Зайдите в голосовой канал!", ephemeral=True)
            return None
        
        channel = inter_obj.author.voice.channel
        
        if inter_obj.guild.voice_client:
            if inter_obj.guild.voice_client.channel == channel:
                logger.info(f"Бот уже в канале {channel.name}.")
                return inter_obj.guild.voice_client
            else:
                try:
                    logger.info(f"Бот перемещается в канал {channel.name}.")
                    await inter_obj.guild.voice_client.move_to(channel)
                    return inter_obj.guild.voice_client
                except Exception as e:
                    logger.error(f"Не могу переместиться в канал: {e}")
                    await _send_dynamic_response(inter_obj, f"❌ Не могу переместиться в канал: {e}", ephemeral=True)
                    return None
        else:
            try:
                logger.info(f"Бот подключается к каналу {channel.name}.")
                voice = await channel.connect()
                return voice
            except Exception as e:
                logger.error(f"Не могу подключиться к каналу: {e}")
                await _send_dynamic_response(inter_obj, f"❌ Не могу подключиться к каналу: {e}", ephemeral=True)
                return None

    async def _process_play_request(self, inter_obj, query: str):
        """Общая логика для команд !play и /play."""
        player = self.get_player(inter_obj.guild)
        voice = await self.connect_voice(inter_obj)
        if not voice:
            # connect_voice уже отправил сообщение об ошибке
            if isinstance(inter_obj, disnake.ApplicationCommandInteraction) and not inter_obj.response.is_done():
                await inter_obj.edit_original_response(content="❌ Не удалось подключиться к голосовому каналу.")
            return
        player.voice = voice

        entry = await player.add(query, inter_obj)
        if entry:
            await player.start_loop()
            # _send_dynamic_response вызывается в player.add, если успешно
            # Также, убедимся, что слэш-командам ответ отправлен
            if isinstance(inter_obj, disnake.ApplicationCommandInteraction) and not inter_obj.response.is_done():
                await inter_obj.edit_original_response(content=f"✅ Добавлено в очередь: **{entry['title']}**")
            elif isinstance(inter_obj, commands.Context): # Только если это обычная команда
                 await _send_dynamic_response(inter_obj, f"✅ Добавлено в очередь: **{entry['title']}**")
        else:
            # player.add уже отправил сообщение об ошибке, если трек не найден
            if isinstance(inter_obj, disnake.ApplicationCommandInteraction) and not inter_obj.response.is_done():
                await inter_obj.edit_original_response(content="❌ Не удалось добавить трек.")

    # --- КОМАНДЫ С ПРЕФИКСОМ (например, !play) ---
    @commands.command(name='play')
    async def play_prefix(self, ctx, *, query: str):
        async with ctx.typing(): # Отображаем "Бот печатает..."
            await self._process_play_request(ctx, query)

    @commands.command(name='skip')
    async def skip_prefix(self, ctx):
        player = self.get_player(ctx.guild)
        if player.voice and (player.voice.is_playing() or player.voice.is_paused()):
            player.voice.stop()
            await ctx.send('⏭️ Трек пропущен.')
        else:
            await ctx.send('❌ Ничего не играет.')

    @commands.command(name='queue')
    async def queue_prefix(self, ctx):
        player = self.get_player(ctx.guild)
        q = list(player.queue._queue)
        
        if not q and not player.current: return await ctx.send('📭 Очередь пуста.')
        
        msg = ""
        if player.current: msg += f"🎶 **Сейчас играет:** {player.current['title']}\n\n"
        if q:
            msg += "**Далее в очереди:**\n"
            for i, item in enumerate(q[:10], 1): msg += f"{i}. {item['title']}\n"
        await ctx.send(msg)

    @commands.command(name='leave')
    async def leave_prefix(self, ctx):
        player = self.get_player(ctx.guild)
        await player.stop()
        await ctx.send('👋 Отключился.')

    # --- СЛЕШ-КОМАНДЫ (например, /play) ---
    @commands.slash_command(name='play', description='Играть музыку (SoundCloud/VK по ссылкам)')
    async def play_slash(self, inter: disnake.ApplicationCommandInteraction, query: str):
        await inter.response.defer() # Отображаем "Бот думает..."
        await self._process_play_request(inter, query)

    @commands.slash_command(name='skip', description='Пропустить текущий трек')
    async def skip_slash(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        player = self.get_player(inter.guild)
        if player.voice and (player.voice.is_playing() or player.voice.is_paused()):
            player.voice.stop()
            await inter.edit_original_response(content='⏭️ Трек пропущен.')
        else:
            await inter.edit_original_response(content='❌ Ничего не играет.')

    @commands.slash_command(name='queue', description='Показать очередь')
    async def queue_slash(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        player = self.get_player(inter.guild)
        q = list(player.queue._queue)
        
        if not q and not player.current: return await inter.edit_original_response(content='📭 Очередь пуста.')
        
        msg = ""
        if player.current: msg += f"🎶 **Сейчас играет:** {player.current['title']}\n\n"
        if q:
            msg += "**Далее в очереди:**\n"
            for i, item in enumerate(q[:10], 1): msg += f"{i}. {item['title']}\n"
        await inter.edit_original_response(content=msg)

    @commands.slash_command(name='leave', description='Выгнать бота из канала')
    async def leave_slash(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        player = self.get_player(inter.guild)
        await player.stop()
        await inter.edit_original_response(content='👋 Отключился.')

def setup(bot):
    bot.add_cog(Music(bot))
