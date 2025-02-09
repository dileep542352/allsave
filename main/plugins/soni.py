#Join t.me/dev_gagan

import logging
import time, os, asyncio
from .. import bot as gagan
from .. import userbot, Bot
from main.plugins.pyroplug import get_bulk_msg
from main.plugins.helpers import get_link
from telethon import events, Button
from pyrogram.errors import FloodWait, PeerIdInvalid

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)

batch = []
ids = []

def clean_channel_id(channel_id):
    """Clean and validate channel ID"""
    try:
        # Remove -100 prefix if exists
        if str(channel_id).startswith('-100'):
            channel_id = str(channel_id)[4:]
        # Ensure valid integer
        return int(channel_id)
    except:
        return None

async def get_messages_safe(client, chat_id, message_id):
    """Safely get messages handling peer ID errors"""
    try:
        # Try with original ID
        return await client.get_messages(chat_id, message_ids=message_id)
    except (PeerIdInvalid, ValueError):
        try:
            # Try with cleaned ID
            cleaned_id = clean_channel_id(chat_id)
            if cleaned_id:
                return await client.get_messages(cleaned_id, message_ids=message_id)
        except:
            pass
    return None

@gagan.on(events.NewMessage(incoming=True, pattern='/batch'))
async def _batch(event):
    s = False
    if f'{event.sender_id}' in batch:
        return await event.reply("You've already started one batch, wait for it to complete!")
    
    async with gagan.conversation(event.chat_id) as conv: 
        if not s:
            await conv.send_message("Send me the message link you want to start saving from, as a reply to this message.", 
                                  buttons=Button.force_reply())
            try:
                link = await conv.get_reply()
                try:
                    _link = get_link(link.text)
                    if not _link:
                        return await conv.send_message("No valid link found.")
                except Exception:
                    return await conv.send_message("No valid link found.")
            except Exception as e:
                logger.info(e)
                return await conv.send_message("Cannot wait more longer for your response!")
            
            await conv.send_message("Send me the number of files/range you want to save from the given message, as a reply to this message.", 
                                  buttons=Button.force_reply())
            try:
                _range = await conv.get_reply()
            except Exception as e:
                logger.info(e)
                return await conv.send_message("Cannot wait more longer for your response!")
            
            try:
                value = int(_range.text)
                if value > 100000:
                    return await conv.send_message("You can only get upto 100000 files in a single batch.")
            except ValueError:
                return await conv.send_message("Range must be an integer!")
            
            for i in range(value):
                ids.append(i)
            
            batch.append(f'{event.sender_id}')
            cd = await conv.send_message("**Batch process ongoing...**\n\nProcess completed: ", 
                                    buttons=[[Button.url("Join Channel", url="http://t.me/dev_gagan")]])
            
            try:
                co = await run_batch(userbot, Bot, event.sender_id, cd, _link)
                if co == -2:
                    await Bot.send_message(event.sender_id, "Batch successfully completed!")
                    await cd.edit(f"**Batch process completed.**\n\nTotal files: {value}")
            except Exception as e:
                await Bot.send_message(event.sender_id, f"ERROR: {str(e)}")
            
            conv.cancel()
            ids.clear()
            batch.clear()

async def run_batch(userbot, client, sender, countdown, link):
    for i in range(len(ids)):
        timer = 2 if i < 250 else 3 if i < 1000 else 4 if i < 10000 else 5 if i < 50000 else 6
        
        if 't.me/c/' not in link:
            timer = 1 if i < 500 else 2
            
        try:
            count_down = f"**Batch process ongoing...**\n\nProcess completed: {i+1}"
            try:
                msg_id = int(link.split("/")[-1])
                chat_id = link.split("/")[-2]
                
                # Clean channel ID
                if 't.me/c/' in link:
                    chat_id = clean_channel_id(chat_id)
                    if not chat_id:
                        return await client.send_message(sender, "**Invalid Channel ID!**")
                
            except ValueError:
                if '?single' not in link:
                    return await client.send_message(sender, "**Invalid Link!**")
                link_ = link.split("?single")[0]
                msg_id = int(link_.split("/")[-1])
                
            integer = msg_id + int(ids[i])
            
            try:
                await get_bulk_msg(userbot, client, sender, link, integer)
                protection = await client.send_message(sender, f"Sleeping for `{timer}` seconds to avoid Floodwaits!")
                await countdown.edit(count_down, 
                                   buttons=[[Button.url("Join Channel", url="https://t.me/dev_gagan")]])
                await asyncio.sleep(timer)
                await protection.delete()
            except PeerIdInvalid:
                # Try with cleaned channel ID
                if chat_id:
                    try:
                        await get_bulk_msg(userbot, client, sender, f"https://t.me/c/{chat_id}/{integer}", integer)
                    except:
                        await client.send_message(sender, "Failed to access channel. Please check the link.")
                        continue
                
        except FloodWait as fw:
            if int(fw.value) > 300:
                await client.send_message(sender, f'You have floodwaits of {fw.value} seconds, cancelling batch')
                ids.clear()
                break
            else:
                fw_alert = await client.send_message(sender, f'Sleeping for {fw.value + 5} second(s) due to floodwait.')
                await asyncio.sleep(fw.value + 5)
                await fw_alert.delete()
                try:
                    await get_bulk_msg(userbot, client, sender, link, integer)
                except Exception as e:
                    logger.info(e)
                    if countdown.text != count_down:
                        await countdown.edit(count_down, 
                                          buttons=[[Button.url("Join Channel", url="http://t.me/dev_gagan")]])
                        
        except Exception as e:
            logger.info(e)
            await client.send_message(sender, f"An error occurred: {str(e)}\nContinuing batch...")
            if countdown.text != count_down:
                await countdown.edit(count_down, 
                                   buttons=[[Button.url("Join Channel", url="https://t.me/dev_gagan")]])
        
        if i + 1 == len(ids):
            return -2

@gagan.on(events.callbackquery.CallbackQuery(data="cancel"))
async def cancel(event):
    ids.clear()
    batch.clear()
    await event.answer("Batch has been cancelled!", alert=True)

START_PIC = "https://telegra.ph/file/1605ca7c742b3f8d2997b.jpg"
TEXT = "👋 Hi, This is 'Paid Restricted Content Saver' bot.\n\nSend /batch to start saving content."

@gagan.on(events.NewMessage(pattern='^/start'))
async def start(event):
    await gagan.send_file(
        event.chat_id,
        file=START_PIC,
        caption=TEXT,
        buttons=[[Button.url("Join Channel", url="https://t.me/dev_gagan")]]
)
