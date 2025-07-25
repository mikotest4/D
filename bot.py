from aiohttp import web
from plugins import web_server
import asyncio
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
import pytz
from datetime import datetime
from config import *
from database.db_premium import *
from database.database import *
from database.db_super_prime import remove_expired_super_prime_users
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

# Suppress APScheduler logs below WARNING level
logging.getLogger("apscheduler").setLevel(logging.WARNING)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.add_job(remove_expired_users, "interval", seconds=10)
scheduler.add_job(remove_expired_super_prime_users, "interval", seconds=300)  # Every 5 minutes

# Reset verify count for all users daily at 00:00 IST
async def daily_reset_task():
    try:
        await db.reset_all_verify_counts()
    except Exception:
        pass  

scheduler.add_job(daily_reset_task, "cron", hour=0, minute=0)
#scheduler.start()


name ="""
 BY Yae Miko
"""

def get_indian_time():
    """Returns the current time in IST."""
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        scheduler.start()
        usr_bot_me = await self.get_me()
        self.username = usr_bot_me.username  # Fix: Add username attribute
        self.uptime = datetime.now()

        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id = db_channel.id, text = "Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER.warning(e)  # Fixed: Remove () after LOGGER
            self.LOGGER.warning(f"Make Sure bot is Admin in DB Channel, and Double check the CHANNEL_ID Value, Current Value {CHANNEL_ID}")  # Fixed: Remove () after LOGGER
            self.LOGGER.info("\nBot Stopped.")  # Fixed: Remove () after LOGGER
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER.info(f"ʙᴏᴛ ʀᴜɴɴɪɴɢ ᴍᴀᴅᴇ ʙʏ ʏᴀᴇ ᴍɪᴋᴏ")  # Fixed: Remove () after LOGGER
    
        # Start Web Server
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()


        try: await self.send_message(OWNER_ID, text = f"<b>𝙼𝚊𝚜𝚝𝚎𝚛 𝚈𝚘𝚞𝚛 𝙱𝚘𝚝 𝙷𝚊𝚜 𝙱𝚎𝚎𝚗 𝚂𝚝𝚊𝚛𝚝𝚎𝚍!</b>")
        except: pass

    async def stop(self, *args):
        await super().stop()
        self.LOGGER.info("Bot stopped.")  # Fixed: Remove () after LOGGER

    def run(self):
        """Run the bot."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start())
        self.LOGGER.info("ʙᴏᴛ ɪs ɴᴏᴡ ʀᴜɴɴɪɴɢ")  # Fixed: Remove () after LOGGER
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.LOGGER.info("sʜᴜᴛᴛɪɴɢ ᴅᴏᴡɴ...")  # Fixed: Remove () after LOGGER
        finally:
            loop.run_until_complete(self.stop())
