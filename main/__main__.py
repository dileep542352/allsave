import logging
import time

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)

botStartTime = time.time()

print("Successfully deployed!")
print("Bot Deployed : Shaurya Soni")

if __name__ == "__main__":
    from . import bot
    import glob
    from pathlib import Path
    from main.utils import load_plugins
    
    path = "main/plugins/*.py"
    files = glob.glob(path)
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem
            load_plugins(plugin_name.replace(".py", ""))
    logger.info("Bot Started Successfully!")
    bot.run_until_disconnected()
