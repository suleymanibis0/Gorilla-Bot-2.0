import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
import logging  
import logging.handlers
import database

logger = logging.getLogger()  # Kök (root) logger'ı al
logger.setLevel(logging.INFO)  # Minimum log seviyesini ayarla (INFO ve üstü)

log_format = '%(asctime)s - [%(levelname)-8s] - %(name)-15s - %(message)s'
formatter = logging.Formatter(log_format)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


file_handler = logging.handlers.RotatingFileHandler(
    filename='discord_bot.log',  
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,
    backupCount=5 
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.WARNING)

load_dotenv()
BOT_TOKEN = os.getenv('DISCORD_TOKEN')


intents = discord.Intents.default()
intents.message_content = True  
intents.members = True


bot = commands.Bot(
    command_prefix="?",
    intents=intents,
    case_insensitive=True
)
bot.remove_command('help')

@bot.event
async def on_command_error(ctx, error):
    """
    Tüm komut hataları burada toplanır ve işlenir.
    """

    if isinstance(error, commands.CommandNotFound):
        await ctx.reply(f"**{ctx.invoked_with}** adında bir komut bulamadım. `?yardım` yazarak listeye bakabilirsin.", delete_after=5)

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f"Eksik bilgi girdin! Doğru kullanım:\n`{ctx.prefix}{ctx.command.name} {ctx.command.signature}`")

    elif isinstance(error, commands.BadArgument):
        await ctx.reply(f"Yanlış formatta bilgi girdin! Doğru kullanım:\n`{ctx.prefix}{ctx.command.name} {ctx.command.signature}`")

    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply("Bu komutu kullanmak için yeterli yetkin yok.")
    
    elif isinstance(error, commands.CommandOnCooldown):
        pass

    else:
        logger.error(f"Beklenmedik hata oluştu: {error}")
        await ctx.reply("Komut çalıştırılırken beklenmedik bir hata oluştu.")


@bot.event
async def on_ready():
    """Bot çalıştırıldığında ve Discord'a başarıyla bağlandığında tetiklenir."""
    print(f"--------------------------------------------------")
    logger.info("Giriş yapıldı!")
    print(f"Bot ID: {bot.user.id}")
    print(f"--------------------------------------------------")
    
    await bot.change_presence(activity=discord.Game(name="?yardım | GELİŞTİRİLME AŞAMASINDA"))

async def load_cogs():
    """'cogs' klasöründeki tüm eklentileri (cog) yükler."""
    print("Coglar yükleniyor...")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f"'{filename}' başarıyla yüklendi.")
            except Exception as e:
                logger.info(f"'{filename}' yüklenirken bir hata oluştu: {e}")
    logger.info("Tüm coglar yüklendi.")

async def main():
    if BOT_TOKEN is None:
        logger.error("HATA: DISCORD_TOKEN bulunamadı. .env dosyasını kontrol edin.")
        return
        
    async with bot:
        await load_cogs()
        await bot.start(BOT_TOKEN)
        print("Bot başlatıldı ve çalışıyor.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot kapatılıyor...")