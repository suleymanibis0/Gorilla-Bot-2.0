import discord
from discord import Member
from discord.ext import commands
import random
import asyncio
import logging
import aiohttp
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import cv

logger = logging.getLogger(__name__)

class Eğlence(commands.Cog):

    def __init__(self, bot: commands.Bot):
        """Bu Cog'un yapıcı (initializer) metodudur."""
        self.bot = bot
        self.giphy_api = "CmufnE1lV4KaDlJd0bKw2FULo7LjFK0i"
        self.client_key= "gorillabot"
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
        logger.info(f"'{__name__}' adlı cog yüklendi.")

    @commands.command(
        name="seçim",
        aliases=["secim", "choice"],
        help="Verilen en az iki seçenek arasında seçim yapar. Örnek: ?seçim pizza hamburger su"
    )
    async def choice(self, ctx: commands.Context, *, secenekler: str):
        secenekler = secenekler.split()
        secilen = random.choice(secenekler)
        await ctx.reply(f"Verdiğin seçeneklerden birisini seçmek zor oldu ama seçimim şu: **{secilen}**")

    @commands.command(name="avatar", help="Etiketlenen kullanıcının avatarını görüntüler.")
    async def avatar(self, ctx: commands.Context, üye : Member = None):
        if üye is None:
            üye = ctx.author
        avatar = üye.display_avatar.url
        await ctx.reply(f"{üye.mention} adlı kullanıcının avatarı")
        await ctx.send(avatar)

    @commands.command(name="gif", help="GIF üretir.")
    async def gif(self, ctx: commands.Context, *, arama: str = "rastgele"):
        
        async with aiohttp.ClientSession() as session:
            if arama == "rastgele":
                url = f"https://api.giphy.com/v1/gifs/random?api_key={self.giphy_api}&tag=&rating=g"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()

                        gif_data = data['data']
                        gif_url = gif_data['images']['original']['url']
                        gif_name = gif_data['title'] or "Rastgele GIF"

                        embed = discord.Embed(title=f"GIF: {gif_name}", color=discord.Color.random())
                        embed.set_image(url=gif_url)
                        embed.set_footer(text=f"{ctx.author.display_name} tarafından istendi via Giphy")
                        
                        await ctx.reply(embed=embed)
                    else:
                        await ctx.reply("API ile iletişim kurulurken bir hata oluştu.")

            else:
                url = f"https://api.giphy.com/v1/gifs/search?api_key={self.giphy_api}&q={arama}&limit=25&offset=0&rating=g&lang=tr&bundle=messaging_non_clips"

                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        gif_listesi = data['data']

                        if len(gif_listesi) > 0:
                            secilen_gif = gif_listesi[0]

                            gif_url = secilen_gif['images']['original']['url']
                            gif_name = secilen_gif['title'] or arama

                            embed = discord.Embed(title=f"GIF: {gif_name}", color=discord.Color.random())
                            embed.set_image(url=gif_url)
                            embed.set_footer(text=f"{ctx.author.display_name} tarafından istendi via Giphy")

                            await ctx.reply(embed=embed)
                        else:
                            await ctx.reply(f"**{arama}** hakkında hiç GIF bulamadım.")
                    else:
                        await ctx.reply("API ile iletişim kurulurken bir hata oluştu.")
        
    @commands.command(name="şarkıöner", aliases=["sarkioner", "onerisarki", "oner", "oneri", "öneri", "öner", "önerişarkı"], help="Şarkı önerisi yapar.")
    async def make_suggestion(self, ctx: commands.Context):
        random_song = random.choice(self.songs)
        embed = discord.Embed(
            title=f"{random_song}",
            color=discord.Color.random()
        )
        embed.add_field(name="Çok güzel şarkıdır.", value=f"`?oynat {random_song}` yazıp dinleyebilirsin.")
        embed.set_footer(text=f"{ctx.author.name} için şarkı önerisi.")

        await ctx.reply(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Eğlence(bot))