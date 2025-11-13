import discord
from discord.ext import commands
import asyncio
import logging

logger = logging.getLogger(__name__)


import discord
from discord.ext import commands
from discord.ui import Select, View

# --- 1. AÇILIR MENÜ (DROPDOWN) SINIFI ---
class YardimDropdown(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        
        # --- AYARLAR (Mapping) ---
        # Cog isimlerine göre emoji ve açıklama ataması yapıyoruz.
        # Eğer buraya yazmadığın bir Cog olursa bot onu varsayılan ayarlarla gösterir.
        cog_data = {
            "Müzik": {"emoji": "🎵", "desc": "Şarkı çalma ve ses yönetimi."},
            "Moderasyon": {"emoji": "🛡️", "desc": "Sunucu güvenliği ve üye yönetimi."},
            "Eğlence": {"emoji": "🎮", "desc": "Oyunlar ve eğlenceli araçlar."},
            "Genel": {"emoji": "📌", "desc": "Genel sunucu komutları."},
            "Ekonomi": {"emoji": "📈", "desc": "Ekonomi ve oyun komutları."}
        }

        options = []

        # 1. 'Ana Sayfa' seçeneğini en başa manuel ekliyoruz
        options.append(discord.SelectOption(
            label="Ana Sayfa",
            description="Yardım menüsü başlangıcına döner.",
            emoji="🏠",
            value="home"
        ))

        # 2. Botun içindeki tüm Cog'ları (Kategorileri) otomatik tarıyoruz
        for cog_name, cog in bot.cogs.items():
            # 'Yardim' kategorisini (kendisini) listede göstermeyelim (Recursion önleme)
            if cog_name == "Bilgi": 
                continue
                
            # İçinde hiç görünür komut olmayan boş kategorileri gizleyelim
            if not any(not c.hidden for c in cog.get_commands()):
                continue

            # Cog verilerini sözlükten çekelim (Yoksa varsayılan değer ata)
            data = cog_data.get(cog_name, {"emoji": "🔧", "desc": "Kategori komutları."})

            # Seçeneği oluşturup listeye ekle
            options.append(discord.SelectOption(
                label=cog_name,  # Label direkt Cog ismi olur (Örn: Müzik)
                description=data["desc"],
                emoji=data["emoji"],
                value=cog_name   # Value direkt Cog ismi olur, böylece bulması kolaylaşır
            ))

        super().__init__(
            placeholder="Bir kategori seçin...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        secim = self.values[0]

        # A. Eğer Ana Sayfa seçildiyse
        if secim == "home":
            embed = discord.Embed(
                title="🤖 Gorilla Bot Yardım",
                description="Aşağıdaki menüden bir kategori seçerek komutları listeleyebilirsiniz.",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            await interaction.response.edit_message(embed=embed, view=self.view)
            return

        # B. Diğer kategoriler seçildiyse (Otomatik Bulma)
        cog = self.bot.get_cog(secim) # Value direkt Cog ismi olduğu için maplemeye gerek kalmadı!
        
        if cog:
            embed = discord.Embed(
                title=f"{secim} Komutları",
                description=f"Aşağıda **{secim}** kategorisine ait komutlar listelenmiştir.",
                color=discord.Color.random()
            )
            
            visible_commands = [c for c in cog.get_commands() if not c.hidden]
            
            # Komutları string haline getir
            # Not: ctx olmadığı için prefix'i manuel alıyoruz veya interaction.client.command_prefix kullanıyoruz
            prefix = "?" 
            
            komut_listesi_1 = ""
            komut_listesi_2 = ""
            for cmd in visible_commands:
                new_list = f"**`{prefix}{cmd.name} {cmd.signature}`** : {cmd.help or 'Açıklama yok.'}\n"
                if len(komut_listesi_1) + len(new_list) < 1024:
                    komut_listesi_1 += new_list
                else:
                    komut_listesi_2 += new_list
            
            embed.add_field(name="Komut Listesi 1", value=komut_listesi_1 or "Gösterilecek komut yok.")

            if komut_listesi_2 != "":
                embed.add_field(name="Komut Listesi 2", value=komut_listesi_2 or "Gösterilecek komut yok.")
            
            await interaction.response.edit_message(embed=embed, view=self.view)
        else:
            await interaction.response.send_message("Bir hata oluştu: Kategori bulunamadı.", ephemeral=True)

# --- 2. VIEW (GÖRÜNÜM) SINIFI ---
class YardimView(discord.ui.View):
    def __init__(self, bot): # View de botu almalı
        super().__init__(timeout=60)
        # Botu Dropdown'a paslıyoruz (Dependency Injection)
        self.add_item(YardimDropdown(bot))

class Bilgi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="yardım", aliases=["help", "yardim", "y", "h"], help="Bu menüyü görmeni sağlar.")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="🤖 Gorilla Bot Yardım", 
            description="Komutları görmek için aşağıdaki menüyü kullanın.",
            color=discord.Color.gold()
        )
        
        # View'i çağırırken botu gönderiyoruz
        view = YardimView(self.bot)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Bilgi(bot))
