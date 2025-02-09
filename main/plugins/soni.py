import logging
import time, os, asyncio
from .. import bot as gagan
from .. import userbot, Bot
from main.plugins.pyroplug import get_bulk_msg
from main.plugins.helpers import get_link
from telethon import events, Button
from pyrogram.errors import FloodWait

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

batch = []
ids = []

@gagan.on(events.NewMessage(incoming=True, pattern='/batch'))
async def _batch(event):
    if f'{event.sender_id}' in batch:
        return await event.reply("You've already started one batch, wait for it to complete!")
    
    async with gagan.conversation(event.chat_id) as conv: 
        try:
            # Get link
            await conv.send_message("Send me the message link you want to start saving from.", 
                                  buttons=Button.force_reply())
            link = await conv.get_reply()
            if not link:
                return await conv.send_message("No response received.")
            
            # Get range
            await conv.send_message("Send me the number of files/range you want to save.", 
                                  buttons=Button.force_reply())
            _range = await conv.get_reply()
            if not _range:
                return await conv.send_message("No response received.")

            try:
                value = int(_range.text)
                if value > 100000:
                    return await conv.send_message("Maximum 100000 files allowed.")
            except ValueError:
                return await conv.send_message("Please send a valid number.")

            # Process the link
            if not 't.me/c/' in link.text:
                return await conv.send_message("Please provide a valid channel link starting with t.me/c/")
            
            try:
                chat_id = link.text.split('/')[4]
                msg_id = int(link.text.split('/')[-1])
                
                # Add to processing queue
                batch.append(f'{event.sender_id}')
                for i in range(value):
                    ids.append(i)
                
                # Start processing
                progress = await conv.send_message("**Batch Process Started**\n\nProcessing: 0", 
                                                 buttons=[[Button.url("Channel", url="https://t.me/dev_gagan")]])
                
                # Process each message
                for i in range(value):
                    try:
                        current_msg_id = msg_id + i
                        await get_bulk_msg(userbot, Bot, event.sender_id, f"https://t.me/c/{chat_id}/{current_msg_id}", current_msg_id)
                        await progress.edit(f"**Batch Process Running**\n\nProcessing: {i+1}/{value}")
                        await asyncio.sleep(2)  # Delay between messages
                    except Exception as e:
                        logger.error(f"Error processing message {current_msg_id}: {str(e)}")
                        continue

                await progress.edit("**Batch Process Completed**")
                
            except Exception as e:
                await conv.send_message(f"An error occurred: {str(e)}")
            
            finally:
                # Cleanup
                if f'{event.sender_id}' in batch:
                    batch.remove(f'{event.sender_id}')
                ids.clear()
                
        except Exception as e:
            await conv.send_message(f"An error occurred: {str(e)}")
        finally:
            conv.cancel()

@gagan.on(events.NewMessage(pattern='^/start'))
async def start(event):
    await event.reply(
        "**Hello! I'm a Channel Content Saver Bot**\n\n"
        "Send /batch to start batch saving process\n\n"
        "Join @dev_gagan for updates!",
        buttons=[[Button.url("Channel", url="https://t.me/dev_gagan")]]
    )

@gagan.on(events.NewMessage(pattern='^/cancel'))
async def cancel(event):
    if f'{event.sender_id}' in batch:
        batch.remove(f'{event.sender_id}')
    ids.clear()
    await event.reply("All processes cancelled!")
