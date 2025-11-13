import discord
from discord import Member
from discord.ext import commands
import random
import asyncio
import logging

logger = logging.getLogger(__name__)


class Moderasyon(commands.Cog):

    def __init__(self, bot: commands.Bot):
        """Bu Cog'un yapıcı (initializer) metodudur."""
        self.bot = bot
        logger.info(f"'{__name__}' adlı cog yüklendi.")

    @commands.command(
        name="temizle",
        aliases=["temizlik", "cls", "clear"],
        help="Belirtilen sayıdaki mesajı temizler."
    )
    async def clear(self, ctx:commands.Context, miktar:str):
        try:
            if miktar == "all" or miktar == "tüm" or miktar == "tum":
                counter = 0
                async for message in ctx.channel.history(limit=None):
                    counter += 1
                
                await ctx.reply("Mesajlar siliniyor...")
                deleted = await ctx.channel.purge(limit=counter + 1)
                
                await ctx.send(f"{len(deleted) - 1} mesaj silindi.", delete_after=5)
            else:
                miktar = int(miktar)
                if miktar <= 0:
                    await ctx.reply(f"Girilen miktar 0'dan küçük ya da 0 olamaz!")
                
                await ctx.reply("Mesajlar siliniyor...")
                deleted = await ctx.channel.purge(limit=miktar + 1)
                await ctx.send(f"{len(deleted) - 1} mesaj silindi.", delete_after=5)
            
            logger.info(f"'{ctx.guild.name}' adlı sunucunun '{ctx.channel.name}' adlı kanalından {len(deleted)-1} kadar mesaj silindi.")
        except Exception as e:
            await ctx.reply(f"Bir şeyler ters gitti.")
            logger.info(f"'{ctx.guild.name}' adlı sunucunun '{ctx.channel.name}' adlı kanalından {len(deleted)-1} kadar mesaj silinirken bir hata oluştu: {e}")

    @commands.command(
        name="ban",
        help="Belirtilen kullanıcıyı sunucudan banlar."
    )
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx:commands.Context, üye: Member, *, sebep: str):
        if ctx.author == üye:
            return await ctx.reply("Kendini sunucudan banlayamazsın.")

        if üye == ctx.me:
            return await ctx.reply("Beni sunucudan banlayamazsın.")
        
        try:
            await üye.send(f"**{ctx.guild.name}** sunucusundan banlandın.\n**Sebep:** {sebep}")
        except discord.Forbidden:
            pass

        try:
            await üye.ban(reason=sebep)
            
            embed = discord.Embed(title="Kullanıcı Banlandı", color=discord.Color.orange())
            embed.add_field(name="Banlanan Kullanıcı", value=üye.mention, inline=False)
            embed.add_field(name="Sebep", value=sebep, inline=False)
            embed.set_footer(text=f"İşlemi yapan: {ctx.author.display_name}")
            
            await ctx.reply(embed=embed)
            logger.info(f"{üye.name} adlı kişi sunucudan {sebep} sebebiyle {ctx.author.mention} tarafından banlandı.")
        except discord.Forbidden:
            await ctx.reply("Bu kullanıcıyı banlamaya **yetkim yetmiyor**. Rolü benim rolümden yüksek olabilir.")
    
    @commands.command(
        name="kick",
        help="Belirtilen kullanıcıyı sunucudan atar."
    )
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx:commands.Context, üye: Member, *, sebep: str):
        if ctx.author == üye:
            return await ctx.reply("Kendini sunucudan atamazsın.")

        if üye == ctx.me:
            return await ctx.reply("Beni sunucudan atamazsın.")
        
        try:
            await üye.send(f"**{ctx.guild.name}** sunucusundan atıldın.\n**Sebep:** {sebep}")
        except discord.Forbidden:
            pass

        try:
            await üye.kick(reason=sebep)
            
            embed = discord.Embed(title="Kullanıcı Atıldı", color=discord.Color.orange())
            embed.add_field(name="Atılan Kullanıcı", value=üye.mention, inline=False)
            embed.add_field(name="Sebep", value=sebep, inline=False)
            embed.set_footer(text=f"İşlemi yapan: {ctx.author.display_name}")
            
            await ctx.reply(embed=embed)
            logger.info(f"{üye.name} adlı kişi sunucudan {sebep} sebebiyle {ctx.author.mention} tarafından atıldı.")
        except discord.Forbidden:
            await ctx.reply("Bu kullanıcıyı atmaya **yetkim yetmiyor**. Rolü benim rolümden yüksek olabilir.")
    
    @commands.command(name="unban", help="Kullanıcının yasağını kaldırır.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, kullanici_bilgisi):
        async for ban_entry in ctx.guild.bans():
            user = ban_entry.user
            
            is_id_match = str(user.id) == kullanici_bilgisi
            is_name_match = user.name == kullanici_bilgisi
            is_name_discrim_match = f"{user.name}#{user.discriminator}" == kullanici_bilgisi

            if is_id_match or is_name_match or is_name_discrim_match:
                await ctx.guild.unban(user)
                

                embed = discord.Embed(title="Yasak Kaldırıldı", color=discord.Color.green())
                embed.add_field(name="Kullanıcı", value=f"{user.name} (ID: {user.id})", inline=False)
                embed.set_footer(text=f"İşlemi yapan: {ctx.author.display_name}")
                
                await ctx.reply(embed=embed)
                return

        await ctx.reply(f"**{kullanici_bilgisi}** adlı kullanıcı yasaklılar listesinde bulunamadı.")

    @kick.error
    @ban.error
    @unban.error
    async def mod_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("Bu komutu kullanmak için gerekli **yetkiye sahip değilsin!**")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Lütfen bir kullanıcı etiketleyin.")
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderasyon(bot))