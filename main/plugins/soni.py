import logging
import time, os, asyncio
from .. import bot as gagan
from .. import userbot, Bot
from telethon import events, Button
from telethon.errors import FloodWaitError

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

batch = []

@gagan.on(events.NewMessage(incoming=True, pattern='/batch'))
async def _batch(event):
    if f'{event.sender_id}' in batch:
        return await event.reply("Already processing a batch!")
    
    async with gagan.conversation(event.chat_id) as conv: 
        try:
            await conv.send_message("Send me the message link to start from.")
            link = await conv.get_reply()
            if not link:
                return await conv.send_message("No response received.")
            
            await conv.send_message("How many messages to process?")
            range_msg = await conv.get_reply()
            if not range_msg:
                return await conv.send_message("No response received.")

            try:
                value = int(range_msg.text)
                if value > 100000:
                    return await conv.send_message("Maximum 100000 messages allowed.")
            except ValueError:
                return await conv.send_message("Please send a valid number.")

            if not 't.me/c/' in link.text:
                return await conv.send_message("Invalid link format. Use channel link format.")
            
            try:
                parts = link.text.split('/')
                channel_id = parts[4]
                start_id = int(parts[5])
                
                batch.append(f'{event.sender_id}')
                progress = await conv.send_message("**⏳ Processing Batch...**\n\n`0` messages done")
                
                success = 0
                for i in range(value):
                    try:
                        msg_id = start_id + i
                        message = await userbot.get_messages(int(channel_id), ids=msg_id)
                        
                        if message and not message.empty:
                            await message.copy(event.chat_id)
                            success += 1
                            if success % 10 == 0:
                                await progress.edit(f"**⏳ Processing Batch...**\n\n`{success}` messages done")
                            await asyncio.sleep(2)
                    except FloodWaitError as e:
                        wait_time = e.seconds
                        await progress.edit(f"**FloodWait:** Waiting for `{wait_time}` seconds")
                        await asyncio.sleep(wait_time)
                    except Exception as e:
                        logger.error(f"Error: {str(e)}")
                        continue

                await progress.edit(f"**✅ Batch Complete**\n\nSuccessfully processed `{success}` messages")
                
            except Exception as e:
                await conv.send_message(f"Error occurred: {str(e)}")
            
            finally:
                if f'{event.sender_id}' in batch:
                    batch.remove(f'{event.sender_id}')
                
        except Exception as e:
            await conv.send_message(f"Error occurred: {str(e)}")
        finally:
            conv.cancel()

@gagan.on(events.NewMessage(pattern='^/start'))
async def start(event):
    await event.reply(
        "**🤖 Channel Content Saver**\n\n"
        "Use /batch to start batch saving\n"
        "Join @dev_gagan for updates",
        buttons=[[Button.url("Updates Channel", url="https://t.me/dev_gagan")]]
    )

@gagan.on(events.NewMessage(pattern='^/cancel'))
async def cancel(event):
    if f'{event.sender_id}' in batch:
        batch.remove(f'{event.sender_id}')
        await event.reply("**Cancelled all processes**")
    else:
        await event.reply("**No active process to cancel**")
