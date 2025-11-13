import discord
from discord.ext import commands
import asyncio
import yt_dlp
import logging
import random
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv

logger = logging.getLogger(__name__)



class Müzik(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sq = {}
        self.history = {}
        try:
            self.songs = cv.get_songs()
            if self.songs is None:
                self.songs = []
                logger.warning("Şarkı listesi boş geldi veya çekilemedi.")
            else:
                logger.info(f"{len(self.songs)} adet şarkı başarıyla yüklendi.")
        except Exception as e:
            self.songs = []
            logger.error(f"Şarkı listesi yüklenirken hata: {e}")
        
        self.ydl = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'default_search': 'auto',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.ffmpeg = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
        }
        logger.info(f"'{__name__}' cog yüklendi.")

    async def search_youtube(self, search: str):
        is_url = search.startswith(('http://', 'https://', 'www.'))
        loop = self.bot.loop
        
        try:
            if is_url:
                data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(self.ydl).extract_info(search, download=False))
            else:
                data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(self.ydl).extract_info(f"ytsearch:{search}", download=False))
                if 'entries' in data:
                    data = data['entries'][0]

            if not data or 'url' not in data:
                return None, None
                
            return data['url'], data.get('title', 'Bilinmeyen Şarkı')

        except Exception as e:
            logger.error(f"YouTube arama hatası: {e}")
            return None, None

    def play_next_song(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        
        if not ctx.voice_client:
            return

        # Eğer kuyrukta şarkı varsa
        if guild_id in self.sq and self.sq[guild_id]:
            # 1. Şarkıyı kuyruktan al (Queue'dan çıkar)
            song = self.sq[guild_id].pop(0)
            song_url = song['url']
            
            # 2. YENİ: Bu şarkıyı geçmişe ekle!
            if guild_id not in self.history:
                self.history[guild_id] = []
            # Listeye ekle (En sona ekleriz, LIFO mantığı ile sondan çekeceğiz)
            self.history[guild_id].append(song) 
            
            try:
                player = discord.FFmpegPCMAudio(song_url, **self.ffmpeg)
                ctx.voice_client.play(player, after=lambda e: self.play_next_song(ctx))
                
                asyncio.run_coroutine_threadsafe(
                    ctx.reply(f"🎵 **Çalınıyor:** `{song['title']}`"), 
                    self.bot.loop
                )
            except Exception as e:
                logger.error(f"Oynatma hatası: {e}")
                # Hata olursa bir sonrakine geçmeyi dene
                self.play_next_song(ctx)
        else:
            asyncio.run_coroutine_threadsafe(
                ctx.reply("✅ Kuyruk bitti."), 
                self.bot.loop
            )

    @commands.command(name='katıl', aliases=['join', 'katil'], help='Botu sesli kanala çağırır.')
    async def join(self, ctx):
        if not ctx.author.voice:
            await ctx.reply(f"{ctx.author.mention}, önce bir ses kanalına girmelisin.")
            return
        
        channel = ctx.author.voice.channel
        voice_client = ctx.guild.voice_client

        if voice_client:
            if voice_client.channel.id != channel.id:
                await voice_client.move_to(channel)
                await ctx.reply(f"**{channel.name}** kanalına taşındım.")
            else:
                await ctx.reply("Zaten seninle aynı kanaldayım!")
        else:
            await channel.connect()
            await ctx.reply(f"**{channel.name}** kanalına katıldım.")

    @commands.command(name='ayrıl', aliases=["leave", "ayril", "cik"], help='Botu kanaldan ayırır.')
    async def leave(self, ctx):
        if ctx.voice_client:
            self.sq[ctx.guild.id] = []
            await ctx.voice_client.disconnect()
            await ctx.reply("Kanaldan ayrıldım.")
        else:
            await ctx.reply("Zaten bir ses kanalında değilim.")

    

    @commands.command(name='oynat', aliases=["play", "çal", "p"], help='Müzik çalar.')
    async def play(self, ctx, *, arama_terimi: str = None):
        if arama_terimi is None:
            arama_terimi = random.choice(self.songs)

            msg = await ctx.reply("🔎 **Rastgele şarkı aranıyor...**")
            await asyncio.sleep(1.5)
            await msg.edit(content=f"✅ **Rastgele şarkı bulundu:** `{arama_terimi}`", delete_after=4)
        
        if not ctx.author.voice:
            return await ctx.reply("Önce bir ses kanalına gir!")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        
        if ctx.voice_client.channel != ctx.author.voice.channel:
             return await ctx.reply("Bot ile aynı kanalda olmalısın.")

        msg = await ctx.reply(f"🔎 **Aranıyor:** `{arama_terimi}`...")
        
        song_url, song_title = await self.search_youtube(arama_terimi)

        if song_url is None:
            return await msg.edit(content="Şarkı bulunamadı veya bir hata oluştu.")

        guild_id = ctx.guild.id
        if guild_id not in self.sq:
            self.sq[guild_id] = []

        # Şarkıyı her türlü kuyruğa ekliyoruz
        song = {'url': song_url, 'title': song_title}
        self.sq[guild_id].append(song)

        await msg.edit(content=f"🎶 **Bulundu ve eklendi:** `{song_title}`")

        # DÜZELTME BURADA:
        # Eğer çalan yoksa manuel başlatmak yerine motoru tetikliyoruz.
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            self.play_next_song(ctx)
        else:
            # Zaten çalıyorsa sadece bilgi veriyoruz (yukarıda zaten ekledik)
            await ctx.reply(f"📝 **Sıraya Eklendi:** `{song_title}`")

    @commands.command(name='önceki', aliases=['back', 'geri', 'onceki', 'previous'], help='Bir önceki şarkıya döner.')
    async def previous_song(self, ctx):
        guild_id = ctx.guild.id
        
        if guild_id in self.history and len(self.history[guild_id]) > 1:
            # Şu an çalan şarkı history'nin sonundadır. Onu oradan çıkarıp çöpe atabiliriz veya tekrar kuyruğa koyabiliriz.
            # Mantık: Geri gitmek istiyorsak, şu an çalanı iptal edip bir öncekini getirmeliyiz.
            
            # Şu an çalanı history'den çıkar (çünkü o artık 'geçmiş' değil 'şimdiki' idi ve iptal edildi)
            curr_song = self.history[guild_id].pop() 
            
            # Şimdi history'nin yeni son elemanı, gerçekten bir önceki şarkıdır.
            previous_song = self.history[guild_id].pop()
            
            # Bu eski şarkıyı kuyruğun EN BAŞINA ekle (Priority Queue)
            if guild_id not in self.sq:
                self.sq[guild_id] = []
            
            self.sq[guild_id].insert(0, previous_song)
            
            # Müziği durdur. (Otomatik olarak play_next_song çalışacak ve 0. sıradaki previous_song çalacak)
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                await ctx.reply("⏮️ Önceki şarkıya dönülüyor...")
            else:
                # Eğer müzik çalmıyorsa manuel tetikle
                self.play_next_song(ctx)
                await ctx.reply("⏮️ Önceki şarkı başlatılıyor...")
        else:
            await ctx.reply("Geçmişte dönecek bir şarkı yok!")

    @commands.command(name='sonraki', aliases=["siradaki","sıradaki", "next"], help='Şarkıyı geçer.')
    async def next_song(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.reply("⏭️ Şarkı geçildi.")
        else:
            await ctx.reply("Şu an geçilecek bir şarkı çalmıyor.")

    @commands.command(
            name='durdur', 
            aliases=["dur", "pause"],
            help='Müziği durdurur. İstenirse `?devamet` komutu ile müzik kaldığı yerden devam eder.'
    )
    async def pause(self, ctx:commands.Context):
        voice_client = ctx.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.reply("⏸️ Müzik duraklatıldı. Devam etmek için `?devamet` yazabilirsin.")
        else:
            await ctx.reply("Şu an zaten çalan bir müzik yok veya bot seste değil.")

    @commands.command(
            name='devamet', 
            aliases=["devam", "resume"],
            help='Müziği kaldığı yerden devam ettirir.'
    )
    async def resume(self, ctx:commands.Context):
        voice_client = ctx.voice_client

        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.reply("▶️ Müzik kaldığı yerden devam ediyor.")
        else:
            await ctx.reply("Şu an duraklatılmış bir müzik yok.")
    
    @commands.command(
            name='bitir', 
            aliases=["bit", "finish"],
            help='Müziği bitirir ve müzik listesini temizler.'
    )
    async def finish(self, ctx):
        if ctx.voice_client:
            self.sq[ctx.guild.id] = []
            ctx.voice_client.stop()
            await ctx.reply("⏹️ Müzik bitirildi ve kuyruk temizlendi.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Müzik(bot))