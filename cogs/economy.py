import discord
from discord import Member
from discord.ext import commands
import database
import random
import asyncio
import logging

logger = logging.getLogger(__name__)

class Ekonomi(commands.Cog):

    def __init__(self, bot: commands.Bot):
        """Bu Cog'un yapıcı (initializer) metodudur."""
        self.bot = bot
        self.db = database.Database("users.db")
        logger.info(f"'{__name__}' adlı cog yüklendi.")
     
    @commands.command(
        name="bakiye",
        aliases=["bal", "balance"],
        help="Sahip olunan bakiyeyi gösterir."
    )
    async def balance(self, ctx: commands.Context, üye: Member = None):
        if üye is None:
            üye = ctx.author
        user_id = str(üye.id)
        user_balance = self.db.get_balance(user_id)
        await ctx.reply(f"İşte {üye.mention} adlı kişinin bakiyesi: {user_balance} coin")

    @commands.command(
        name="çarkçevir",
        aliases=["çark", "cark", "wheel"],
        help="Çark çevirirsen 3 büyük hediyeden birini kazanabilirsin\nama dikkat et paranın çoğunu kaybetme olsaılığın da var. Ayrıca çark ücreti 10.000 coindir."
    )
    async def wheel(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        current_balance = self.db.get_balance(user_id)

        if current_balance < 10000:
            await ctx.reply("Çark çevirebilmek için en az 10.000 coine sahip olman gerek.")
            return
        
        possibilities = [10000, 25000, 50000, 100000, "iflas", "50iflas", "25iflas"]
        result = random.choice(possibilities)

        await ctx.reply("Çark çeviriliyor... 🎡")
        await asyncio.sleep(1)
        
        new_balance = 0
        message = ""
        log_msg = ""

        match result:
            case 10000:
                new_balance = self.db.update_balance(user_id, 10000)
                message = f"Tebrikler {ctx.author.mention} 10.000 para kazandın."
                log_msg = f"{ctx.author.name} çark çevirdi ve 10.000 Coin kazandı."
            case 25000:
                new_balance = self.db.update_balance(user_id, 25000)
                message = f"Tebrikler {ctx.author.mention} 25.000 para kazandın."
                log_msg = f"{ctx.author.name} çark çevirdi ve 25.000 Coin kazandı."
            case 50000:
                new_balance = self.db.update_balance(user_id, 50000)
                message = f"Tebrikler {ctx.author.mention} 50.000 para kazandın."
                log_msg = f"{ctx.author.name} çark çevirdi ve 50.000 Coin kazandı."
            case 100000:
                new_balance = self.db.update_balance(user_id, 100000)
                message = f"Tebrikler {ctx.author.mention} 100.000 para kazandın."
                log_msg = f"{ctx.author.name} çark çevirdi ve 100.000 Coin kazandı."
            case "iflas":
                # <--- DÜZELTME: Mevcut bakiyeyi kullan
                new_balance = self.db.update_balance(user_id, -current_balance) 
                message = f"Ne yazık ki tüm paranı kaybettin {ctx.author.mention}."
                log_msg = f"{ctx.author.name} çark çevirdi ve {current_balance} kaybetti."
            case "50iflas":
                miktar_to_lose = -int(current_balance * 0.5)
                new_balance = self.db.update_balance(user_id, miktar_to_lose)
                message = f"Ne yazık ki paranın yarısını kaybettin {ctx.author.mention}."
                log_msg = f"{ctx.author.name} çark çevirdi ve {-miktar_to_lose} kaybetti."
            case "25iflas":
                miktar_to_lose = -int(current_balance * 0.25)
                new_balance = self.db.update_balance(user_id, miktar_to_lose)
                message = f"Ne yazık ki paranın çeyreğini kaybettin {ctx.author.mention}."
                log_msg = f"{ctx.author.name} çark çevirdi ve {-miktar_to_lose} kaybetti."
        
        await ctx.reply(f"{message} İşte güncel bakiyen: {new_balance} Coin")
        logger.info(log_msg)

    @commands.command(
        name="al",
        aliases=["buy", "alış"],
        help="""Alınabilen eşyaları eğer para yetiyorsa alır.
        Her eşya kullanıcının belirli bir özelliğe sahip olmasını sağlar.
        Alınabilen eşyaları ve özelliklerini görmek için ?market yaz."""
    )
    async def buy(self, ctx: commands.Context ,miktar: int, *, eşya: str):
        
        if miktar <= 0: # <--- YENİ: Negatif alım kontrolü
            await ctx.reply("En az 1 tane alabilirsin.")
            return

        user_id = str(ctx.author.id)
        user_balance = self.db.get_balance(user_id)
        
        # <--- DÜZELTME: self.db.db değil, self.db
        price = self.db.get_item_price(eşya)
        
        # <--- DÜZELTME: Eşya yoksa (None) kontrolü
        if price is None:
            await ctx.reply(f"`{eşya}` adında bir eşya markette bulunamadı.")
            return
            
        # <--- DÜZELTME: Miktarı (miktar) hesaba kat
        total_cost = price * miktar
        
        if user_balance >= total_cost: # <--- DÜZELTME: >= olmalı
            # Parayı düş
            self.db.update_balance(user_id, -total_cost)
            # Eşyayı ekle
            self.db.update_item_count(user_id, eşya, miktar)
            await ctx.reply(f"`{eşya}` eşyasından {total_cost} coin karşılığında {miktar} tane satın alındı.")
            log_msg = f"{ctx.author.name} {total_cost} coin karşılığında {eşya} öğesini satın aldı."
        else:
            await ctx.reply(f"Yetersiz bakiye. Gerekli: {total_cost} Coin, Sende olan: {user_balance} Coin")
            log_msg = f"{ctx.author.name} {total_cost} coin karşılığında {eşya} öğesini bakiye yetersizliğinden dolayı satın alamadı."
        
        logger.info(log_msg)
    
    @commands.command(
        name="envanter",
        aliases=["inventory", "inv"],
        help="Kullanıcının envanterini gösterir."
    )
    async def inventory(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        
        # 1. Eşyaları (items_users tablosundan) al
        inventory = self.db.get_user_inventory(user_id) 
        
        # 2. Kasa sayısını (users tablosundan) al
        case_count = self.db.get_cases(user_id)

        description_lines = [] # <--- YENİ: Açıklama için bir liste oluşturalım

        if inventory: # dict boş değilse eşyaları ekle
            description_lines.extend([f"**{item}**: {count} adet" for item, count in inventory.items()])
        
        # <--- YENİ: Kasa sayısını her zaman göster (0 olsa bile)
        description_lines.append(f"**Kasa**: {case_count} adet 📦")
        
        # <--- DÜZELTME: Eğer envanter (items) boşsa VE kasa sayısı 0 ise "boş" de
        if not inventory and case_count == 0:
            await ctx.reply("Envanterin boş. `?market` yazarak eşyalara bakabilirsin.")
            return

        inv_str = "\n".join(description_lines)
        
        embed = discord.Embed(
            title=f"{ctx.author.name}'ın Envanteri 🎒",
            description=inv_str,
            color=discord.Color.blue()
        )
        await ctx.reply(embed=embed)
    
    @commands.command(
        name="market",
        help="Marketteki eşyaları listeler."
    )
    async def market(self, ctx: commands.Context):

        items = self.db.get_all_items()
        
        if items: 
            market_str = "\n".join([
                f"**{item}**: {details['price']} Coin --> *Özellik: {details['description']}*" 
                for item, details in items.items()
            ])
            
            embed = discord.Embed(
                title="🛒 Market",
                description=market_str,
                color=discord.Color.green()
            )
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("Market şu anda boş.")
    
    @commands.command(
        name="günlüködül",
        aliases=["gunluk", "gunlukodul", "daily", "dailyreward"],
        help="Günlük olarak ödül almanızı sağlar."
    )
    @commands.cooldown(1, 86400, commands.BucketType.user) 
    async def daily(self, ctx: commands.Context):
        
        # <--- DÜZELTME: ID'yi en başta str yapalım ve tek bir değişken kullanalım
        user_id = str(ctx.author.id) 
        
        reward_money = 1000
        reward_cases = 1
        message = "" # <--- YENİ: Mesajı tek bir değişkende tutalım
        log_msg = ""

        # <--- DÜZELTME: user_id kullanalım
        if "Umidi Zı Babo Men" in self.db.get_user_inventory(user_id).keys():
            reward_money = 9000
            reward_cases = 3
            # <--- DÜZELTME: await ctx.reply kullanın ve mesajı değişkene atayın
            message = f"Tebrikler **Umidi Zı Babo Men** eşyası sende olduğu için {reward_money} Coin ve {reward_cases} kasa kazandın."
            log_msg = f"{ctx.author.name} arttırılmış günlük ödül aldı."
        else:
            # <--- DÜZELTME: Normal ödül mesajı
            message = f"Tebrikler bugün {reward_money} Coin ve {reward_cases} kasa kazandın."
            log_msg = f"{ctx.author.name} günlük ödül aldı."
        
        # Veritabanı güncellemesini IF bloğunun DIŞINDA yapalım
        self.db.update_balance(user_id, reward_money)
        self.db.update_cases(user_id, reward_cases)
        
        logger.info(log_msg)
        # <--- DÜZELTME: Mesajı tek seferde gönder
        await ctx.reply(message)

    @daily.error
    async def daily_error(self, ctx, error):
        log_msg = ""
        if isinstance(error, commands.CommandOnCooldown):
            # Kalan süreyi formatlayalım (saat, dakika, saniye)
            kalan_saniye = int(error.retry_after)
            saat = kalan_saniye // 3600
            kalan_saniye %= 3600
            dakika = kalan_saniye // 60
            saniye = kalan_saniye % 60
            
            await ctx.reply(f"Bu komutu tekrar kullanmak için **{saat} saat {dakika} dakika {saniye} saniye** beklemelisin.")
            log_msg = f"{ctx.author.name} günlük ödül alamadı."
        else:
            # Diğer hatalar için
            await ctx.reply(f"Bir hata oluştu. Lütfen bot yapımcısına bildiriniz.")
            log_msg = f"{ctx.author.name} günlük ödül alırken bir hata oluştu: {error}"
        
        logger.exception(log_msg)
    
    @commands.command(
        name="kasaaç",
        aliases=["kasa", "kasaac"],
        help="Eğer envanterinizde kasa varsa girilen miktar kadar kasa açar. Eğer miktar girilmezse 1 kasa açar."
    )
    async def case(self, ctx: commands.Context, miktar:int=1):
        # <--- DÜZELTME: ID'yi en başta str yapalım
        user_id = str(ctx.author.id) 
        
        # <--- KRİTİK DÜZELTME: user_id parametresi eksik!
        current_cases = self.db.get_cases(user_id) 
        
        case_contents = {"İbo'nun Steteskopu": 3,
                        "Hacı'nın Aleti" : 5,
                         "Benim Adım Cafer": 10,
                         "Umidi Zı Babo Men": 12,
                         "Burak Yılmaz": 15,
                         1000: 15,
                         10000: 10,
                         31000: 8,
                         100000: 2,
                         100: 25,
                         75000: 5}
        
        if miktar <= 0:
            await ctx.reply(f"Lütfen sıfırdan büyük bir değer giriniz!")
            return
        
        if miktar > current_cases:
            await ctx.reply(f"Bu kadar kasaya sahip değilsiniz. Sahip olduğunuz kasa sayısı: **{current_cases}**")
            return
        
        while 0<miktar<=current_cases:
                # <--- KRİTİK DÜZELTME: user_id ve miktar (-1) parametreleri eksik!
            self.db.update_cases(user_id, -1) 
            
            # <--- KRİTİK DÜZELTME: Ağırlıklı rastgele seçim mantığı
            # items = ['Hacı'nın Aleti', 'Benim Adım Cafer', 1000, ...]
            items = list(case_contents.keys()) 
            # weights = [5, 13, 15, ...]
            weights = list(case_contents.values())
            
            # random.choices bir liste döner (örn: ['Hacı'nın Aleti']), 
            # bu yüzden [0] ile içinden tekil elemanı alırız.
            reward = random.choices(items, weights=weights, k=1)[0]

            # <--- DÜZELTME: '== True' gereksizdir
            if isinstance(reward, str): 
                # <--- DÜZELTME: user_id kullanalım
                if self.db.get_item_count(user_id, reward) == 0: 
                    
                    # <--- KRİTİK DÜZELTME: 'miktar' (miktar) parametresi eksik!
                    self.db.update_item_count(user_id, reward, 1) 
                    await ctx.reply(f"Tebrikler 1 adet **{reward}** kazandınız!")
                    log_msg = f"{ctx.author.name} kasa açtı ve {reward} kazandı."

                else:
                    # <--- DÜZELTME: user_id kullanalım
                    self.db.update_balance(user_id, 10000) 
                    await ctx.reply(f"Tebrikler 1 adet **{reward}** kazandınız fakat bu ödüle sahip olduğunuz için ödül **10000** Coin olarak bakiyenize eklendi.")
                    log_msg = f"{ctx.author.name} kasa açtı ve {reward} kazandı ama kullanamıyor."
            else: # Ödül string değilse (yani para ise)
                # <--- DÜZELTME: user_id kullanalım
                self.db.update_balance(user_id, reward)
                # <--- DÜZELTME: user_id kullanalım
                await ctx.reply(f"Tebrikler **{reward}** Coin kazandınız! İşte yeni bakiyeniz: {self.db.get_balance(user_id)} Coin")
                log_msg = f"{ctx.author.name} kasa açtı ve {reward} coin kazandı."
            
            
            miktar -= 1
            logger.info(log_msg)

    @commands.command(
        name="slot",
        aliases=["s"],
        help="Eğer üç simgeyi yan yana getirirsen paranı katlayabilirsin. Ayrıca yanlarda gelen 2 simge aynı olur diğeri farklı olursa da para kazanma ihtimalin var."
    )
    async def slot(self, ctx: commands.Context, miktar: int):
        id = ctx.author.id
        current_balance = self.db.get_balance(id)

        if miktar <= 0:
            await ctx.reply("Bahis miktarı pozitif olmalı.")
            return
        if not miktar <= self.db.get_balance(id):
            await ctx.reply(f"Yetersiz bakiye! Bakiyen: {current_balance} Coin")
            return
        
        self.db.update_balance(id, -miktar)
        symbols = ["🍒", "🍓", "​🍑", "💩"]
        weights = [35, 30, 25, 15]
        multipliers = {
            "🍒": 3, "🍓": 5, "​🍑": 10, "💩": 0
        }

        results = random.choices(symbols, weights=weights, k=3)
        result1 = results[0]
        result2 = results[1]
        result3 = results[2]

        def get_view(a,b,c,d,e):
            return f"""    
            `      SLOT      `{d}
`|  ` {a}{b}{c} `  |`{e}
`                `"""


        # embed = discord.Embed(
        #     title="🎰  SLOT MACHINE  🎰",
        #     description="❓ | ❓  | ❓",
        #     color=discord.Color.from_rgb(0, 255, 200)
        # )
        # embed.set_footer(text=f"{ctx.author.name} tarafından oynandı.")
        
        # embed1 = discord.Embed(
        #     title="🎰  SLOT MACHINE  🎰",
        #     description=f"{result1} | ❓  | ❓",
        #     color=discord.Color.from_rgb(0, 255, 200)
        # )
        # embed1.set_footer(text=f"{ctx.author.name} tarafından oynandı.")

        # embed2 = discord.Embed(
        #     title="🎰  SLOT MACHINE  🎰",
        #     description=f"{result1} | {result2}  | ❓",
        #     color=discord.Color.from_rgb(0, 255, 200)
        # )
        # embed2.set_footer(text=f"{ctx.author.name} tarafından oynandı.")

        embed3 = discord.Embed(
            title="🎰  SLOT MACHINE  🎰",
            description=f"{result1} | {result2}  | {result3}",
            color=discord.Color.from_rgb(0, 255, 200)
        )
        embed3.set_footer(text=f"{ctx.author.name} tarafından oynandı.")

        msg = await ctx.reply(get_view("❓", "❓", "❓", "", ""))
        await asyncio.sleep(0.5)
        await msg.edit(content=get_view(result1, "❓", "❓", "", ""))
        await asyncio.sleep(0.5)
        await msg.edit(content=get_view(result1, result2, "❓", "", ""))
        await asyncio.sleep(0.5)
        await msg.edit(content=get_view(result1, result2, result3, "", ""))
        msg_ = ""
        if result1 == result2 == result3:
            multiplier = multipliers.get(result1)
            if multiplier > 0:
                reward = miktar * multiplier
                self.db.update_balance(id, int(reward))
                log_msg = f"{ctx.author.name} slot oynadı, jackpot geldi ve {int(reward)} coin kazandı."
            
                
            else:
                log_msg = f"{ctx.author.name} slot oynadı ve ne kazandı ne kaybetti."
            
            msg_ = get_view(result1, result2, result3, f"    {ctx.author.name} {miktar}  💵  yatırdı", f"    ve {int(reward)}  💵  kazandı.")
        
        elif result1 == result2 or result2 == result3:
            multiplier = multipliers.get(result2)
            if multiplier > 0:
            
                reward = miktar * 1.5
                self.db.update_balance(id, int(reward))
                log_msg = f"{ctx.author.name} slot oynadı, yarı jackpot geldi ve {int(reward)} coin kazandı."
            
            else:
                reward = miktar * 0.5
                self.db.update_balance(id, int(reward))
                log_msg = f"{ctx.author.name} slot oynadı ve yatırılan paranın yarısını kaybetti."
            
            msg_ = get_view(result1, result2, result3, f"    {ctx.author.name} {miktar}  💵  yatırdı", f"    ve {int(reward)}  💵  kazandı.")
        
        else:
            msg_ = get_view(result1, result2, result3, f"    {ctx.author.name} {miktar}  💵  yatırdı", f"    ve hiçbir şey kazanamadı :(")
            log_msg = f"{ctx.author.name} slot oynadı ve {miktar} coin kaybetti."
        
        current_balance = self.db.get_balance(id)
        logger.info(log_msg)
        
        await msg.edit(content=msg_)

    @commands.command(
        name="yazıtura",
        aliases=["yazitura", "coinflip"],
        help="Eğer tahmini doğru yaparsan yatırdığının üç katı para alırsın."
    )
    async def coinflip(self, ctx: commands.Context, hamle: str, miktar:int):
        id = str(ctx.author.id)
        current_balance = self.db.get_balance(id)
        moves = ["yazı", "tura"]
        result = random.choice(moves)
        hamle = hamle.lower()

        if hamle not in moves:
            await ctx.reply("Lütfen `yazı` ya da `tura` yazınız.")
            return

        if current_balance < miktar:
            await ctx.reply("Girdiğin miktarın bakiyenden az olması gerekir.")
            return

        new_balance = self.db.update_balance(id, -miktar)
        msg = await ctx.reply("🪙 Parayı attım bir saniye...")
        await asyncio.sleep(1)

        if hamle == result:
            new_balance = self.db.update_balance(id, 3 * miktar)
            await msg.edit(content=f"🎉  `{result.capitalize()}` geldi kazandın. Yeni bakiyen: {new_balance}")

        else:
            await msg.edit(content=f"😨  `{result.capitalize()}` geldi kaybettin. Yeni bakiyen: {new_balance}")

    @commands.command(
        name="eft",
        aliases=["paragonder", "sendmoney", "paragönder"],
        help="Belirtilen kullanıcıya bekiyenizden para gönderirsiniz."
    )
    async def sendmoney(self, ctx:commands.Context, üye: discord.Member, miktar:int):
        from_id = ctx.author.id
        to_id = üye.id
        from_balance = self.db.get_balance(from_id)

        msg = await ctx.reply(f"{ctx.author.mention} adlı kullanıcıdan {üye.mention} adlı kullanıcıya {miktar} coin gönderiliyor...")
        await asyncio.sleep(2)
        if from_balance >= miktar:
            await msg.edit(content=f"EFT gerçekleşiyor...")
            await asyncio.sleep(2)
            self.db.update_balance(from_id, -miktar)
            self.db.update_balance(to_id, miktar)
            await msg.edit(content=f"{üye.mention} adlı kullanıcıya yapılan EFT işlemi başarıyla gerçekleşmiştir. Gönderilen miktar: {miktar} coin")
        else:
            await ctx.reply(f"EFT gerçekleşirken bir hata oluştu. Bakiyen yetersiz!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Ekonomi(bot))