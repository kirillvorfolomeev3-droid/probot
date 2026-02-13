import disnake
from disnake.ext import commands
import random
import asyncio

class MafiaVoteView(disnake.ui.View):
    """Класс для голосования (выпадающее меню)"""
    def __init__(self, players, title="Выберите игрока"):
        super().__init__(timeout=60)
        self.chosen_member = None
        
        # Создаем выпадающее меню со списком живых игроков
        options = [
            disnake.SelectOption(label=p.display_name, value=str(p.id)) 
            for p in players
        ]
        
        self.select = disnake.ui.Select(placeholder=title, options=options)
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, inter: disnake.MessageInteraction):
        self.chosen_member = self.select.values[0]
        await inter.response.send_message(f"Выбор принят!", ephemeral=True)
        self.stop()

class MafiaJoinView(disnake.ui.View):
    """Лобби для сбора игроков"""
    def __init__(self):
        super().__init__(timeout=10)
        self.players = []

    @disnake.ui.button(label="Участвовать", style=disnake.ButtonStyle.green)
    async def join(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author not in self.players:
            self.players.append(inter.author)
            await inter.response.send_message("Вы записались!", ephemeral=True)
        else:
            await inter.response.send_message("Вы уже в игре.", ephemeral=True)

class Mafia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def start_mafia_logic(self, ctx_or_inter):
        # 1. СБОР ИГРОКОВ
        view = MafiaJoinView()
        embed = disnake.Embed(title="🕵️ Мафия: Сбор игроков", description="Нажмите кнопку, чтобы зайти в игру (мин. 3 игрока для теста, лучше 4+)", color=0x2f3136)
        
        if isinstance(ctx_or_inter, disnake.Interaction):
            await ctx_or_inter.response.send_message(embed=embed, view=view)
            msg = await ctx_or_inter.original_message()
        else:
            msg = await ctx_or_inter.send(embed=embed, view=view)

        await asyncio.sleep(10) # Ждем 20 сек (для теста можно меньше)
        view.stop()
        
        players = view.players
        if len(players) < 3:
            return await msg.edit(content="❌ Игра отменена: мало игроков.", embed=None, view=None)

        # 2. РАСПРЕДЕЛЕНИЕ РОЛЕЙ
        random.shuffle(players)
        mafia = players[0]
        civilians = players[1:]
        alive_players = list(players)

        await msg.edit(content="🎭 Роли распределены! Игра началась. Мафия получила инструкции в ЛС.", embed=None, view=None)
        try:
            await mafia.send("🔴 ТЫ МАФИЯ! Твоя цель — убить всех мирных. Ночью ты будешь выбирать жертву.")
        except: pass

        # 3. ИГРОВОЙ ЦИКЛ
        while True:
            # --- НОЧЬ ---
            await msg.channel.send("🌃 **Наступает ночь... Город засыпает. Просыпается мафия.**")
            
            # Мафия выбирает жертву через ЛС
            vote_view = MafiaVoteView([p for p in alive_players if p != mafia], "Кого убить?")
            try:
                await mafia.send("Кого хочешь устранить этой ночью?", view=vote_view)
            except:
                await msg.channel.send("⚠️ Мафия не открыла ЛС! Ночь пропущена.")
                vote_view.chosen_member = None

            await asyncio.sleep(40) # Ждем выбора мафии
            
            victim_id = vote_view.chosen_member
            victim = None
            if victim_id:
                victim = next((p for p in alive_players if str(p.id) == victim_id), None)
                if victim:
                    alive_players.remove(victim)

            # --- ДЕНЬ ---
            await msg.channel.send("🌅 **Город просыпается...**")
            if victim:
                await msg.channel.send(f"💀 К сожалению, этой ночью был убит {victim.mention}. Он был мирным жителем.")
            else:
                await msg.channel.send("🕊️ Этой ночью никто не погиб.")

            # Проверка победы мафии
            if len(alive_players) <= 2 and mafia in alive_players:
                await msg.channel.send(f"🚩 **МАФИЯ ПОБЕДИЛА!** {mafia.mention} перебил всех.")
                break

            # --- ГОЛОСОВАНИЕ ---
            await msg.channel.send("⚖️ **Время голосования!** Обсудите и решите, кто мафия. У вас 20 секунд.")
            await asyncio.sleep(20)
            
            day_vote_view = MafiaVoteView(alive_players, "Проголосовать против...")
            voting_msg = await msg.channel.send("Выберите игрока, которого вы подозреваете:", view=day_vote_view)
            
            await asyncio.sleep(20)
            
            executed_id = day_vote_view.chosen_member
            if executed_id:
                executed = next((p for p in alive_players if str(p.id) == executed_id), None)
                if executed:
                    alive_players.remove(executed)
                    await msg.channel.send(f"📢 Город решил казнить {executed.mention}...")
                    
                    if executed == mafia:
                        await msg.channel.send("🎉 **МИРНЫЕ ПОБЕДИЛИ!** Мафия была поймана.")
                        break
                    else:
                        await msg.channel.send("😱 Он был мирным жителем... Игра продолжается.")
                else:
                    await msg.channel.send("Никого не казнили: выбор не сделан.")
            else:
                await msg.channel.send("Никого не казнили: город не успел проголосовать.")

            # Проверка победы мафии после голосования
            if len(alive_players) <= 1:
                await msg.channel.send("🚩 **МАФИЯ ПОБЕДИЛА!**")
                break

    @commands.slash_command(name="mafya")
    async def slash_mafya(self, inter):
        await self.start_mafia_logic(inter)

    @commands.command(name="mafya")
    async def prefix_mafya(self, ctx):
        await self.start_mafia_logic(ctx)

def setup(bot):
    bot.add_cog(Mafia(bot))

