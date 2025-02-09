#Developer : Gagan 

import time, os
import logging
import json
from .. import bot as gagan
from .. import userbot, Bot
from main.plugins.pyroplug import get_msg
from main.plugins.helpers import get_link, join, screenshot

from telethon import events
from pyrogram.errors import FloodWait, PeerIdInvalid

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.INFO)
logging.getLogger("telethon").setLevel(logging.INFO)

message = "Send me the message link you want to start saving from, as a reply to this message."
          
process = []
timer = []
user = []

def normalize_chat_id(chat_id):
    """Normalize channel/chat ID by ensuring proper format"""
    try:
        chat_id = str(chat_id).replace("-100", "")
        if not chat_id.isdigit():
            raise ValueError("Invalid channel ID")
        return int('-100' + chat_id)
    except Exception as e:
        raise ValueError(f"Invalid channel ID: {str(e)}")

@gagan.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def clone(event):
    logging.info(event)
    file_name = ''
    if event.is_reply:
        reply = await event.get_reply_message()
        if reply.text == message:
            return

    lit = event.text
    li = lit.split("\n")
    if len(li) > 10:
        await event.reply("max 10 links per message")
        return

    for li in li:
        try:
            link = get_link(li)
            if not link:
                continue
        except TypeError:
            continue
            
        edit = await event.reply("Processing!")
        if f'{int(event.sender_id)}' in user:
            await edit.edit("Please don't spam links, wait until ongoing process is done.")
            return
        
        try:
            user.append(f'{int(event.sender_id)}')
            
            if "|" in li:
                url = li
                url_parts = url.split("|")
                if len(url_parts) == 2:
                    file_name = url_parts[1].strip()
                    
            if 't.me/' not in link:
                await edit.edit("invalid link")
                continue
                
            if 't.me/+' in link:
                q = await join(userbot, link)
                await edit.edit(q)
                continue
                
            msg_id = 0
            try:
                msg_id = int(link.split("/")[-1])
            except ValueError:
                if '?single' in link:
                    link_ = link.split("?single")[0]
                    msg_id = int(link_.split("/")[-1])
                else:
                    msg_id = -1
                    
            if msg_id == -1:
                await edit.edit("Invalid message ID")
                continue
                
            try:
                if 't.me/c/' in link:
                    chat_id = link.split("/")[-2]
                    try:
                        chat_id = normalize_chat_id(chat_id)
                        await userbot.get_chat(chat_id)
                    except ValueError as e:
                        await edit.edit(str(e))
                        continue
                    except PeerIdInvalid:
                        await edit.edit("Invalid channel/group ID")
                        continue
                
                await get_msg(userbot, Bot, event.sender_id, edit.id, link, msg_id, file_name)
                
            except ValueError as ve:
                if "Peer id invalid" in str(ve):
                    await edit.edit("Invalid channel/chat ID. Please check the link.")
                    continue
                raise
                
        except FloodWait as fw:
            await edit.edit(f'Try again after {fw.value} seconds due to floodwait from telegram.')
            
        except Exception as e:
            logging.error(f"Error: {str(e)}", exc_info=True)
            await edit.edit(f"An error occurred: {str(e)}")
            
        finally:
            if f'{int(event.sender_id)}' in user:
                ind = user.index(f'{int(event.sender_id)}')
                user.pop(int(ind))
            time.sleep(1)
