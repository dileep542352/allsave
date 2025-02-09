import asyncio, time, os
from pyrogram.enums import ParseMode, MessageMediaType
from .. import Bot, bot
from main.plugins.progress import progress_for_pyrogram
from main.plugins.helpers import screenshot
from pyrogram import Client, filters
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid, FloodWait
from main.plugins.helpers import video_metadata
from telethon import events
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.INFO)
logging.getLogger("telethon").setLevel(logging.INFO)

async def check(userbot, client, link):
    try:
        msg_id = 0
        try:
            msg_id = int(link.split("/")[-1])
        except ValueError:
            if '?single' not in link:
                return False, "**Invalid Link!**"
            link_ = link.split("?single")[0]
            msg_id = int(link_.split("/")[-1])
            
        if 't.me/c/' in link:
            chat_id = link.split("/")[-2]
            if not chat_id.isdigit():
                return False, "Invalid channel ID"
            chat = int('-100' + str(chat_id))
            try:
                await userbot.get_chat(chat)
                await userbot.get_messages(chat, msg_id)
                return True, None
            except ValueError:
                return False, "Invalid channel ID"
            except Exception as e:
                logging.error(e)
                return False, "Have you joined the channel?"
        else:
            try:
                chat = str(link.split("/")[-2])
                await client.get_messages(chat, msg_id)
                return True, None
            except Exception as e:
                logging.error(e)
                return False, "Maybe bot is banned from the chat, or your link is invalid!"
    except Exception as e:
        logging.error(e)
        return False, "An error occurred while checking the link"

async def get_msg(userbot, client, sender, edit_id, msg_link, i, file_n):
    try:
        if 't.me/c/' in msg_link or 't.me/b/' in msg_link:
            if "t.me/b" not in msg_link:    
                chat_id = msg_link.split("/")[-2]
                chat = int('-100' + str(chat_id))
                try:
                    await userbot.get_chat(chat)
                except ValueError:
                    await client.edit_message_text(sender, edit_id, "Invalid channel ID")
                    return None
            else:
                chat = int(msg_link.split("/")[-2])
                
            try:
                msg = await userbot.get_messages(chat_id=chat, message_ids=i)
                
                if msg.service is not None or msg.empty is not None:
                    await client.delete_messages(chat_id=sender, message_ids=edit_id)
                    return None
                    
                if msg.media and msg.media == MessageMediaType.WEB_PAGE:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await client.send_message(sender, msg.text.markdown, parse_mode=ParseMode.MARKDOWN)
                    await edit.delete()
                    return None
                    
                if not msg.media and msg.text:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await client.send_message(sender, msg.text.markdown, parse_mode=ParseMode.MARKDOWN)
                    await edit.delete()
                    return None
                    
                if msg.media == MessageMediaType.POLL:
                    await client.edit_message_text(sender, edit_id, 'Poll media cannot be saved')
                    return None
                    
                edit = await client.edit_message_text(sender, edit_id, "Trying to Download.")
                
                file = await userbot.download_media(
                    msg,
                    progress=progress_for_pyrogram,
                    progress_args=(client, "**Downloading...**\n", edit, time.time())
                )
                
                # Rest of your existing file handling code...
                # (The file processing, uploading, and cleanup code remains the same)
                
            except Exception as e:
                logging.error(f"Error processing message: {str(e)}", exc_info=True)
                await client.edit_message_text(sender, edit_id, f"Error processing message: {str(e)}")
                return None
                
        else:
            edit = await client.edit_message_text(sender, edit_id, "Cloning.")
            chat = msg_link.split("/")[-2]
            await client.copy_message(sender, chat, i)
            await edit.delete()
            
    except ValueError as ve:
        if "Peer id invalid" in str(ve):
            await client.edit_message_text(sender, edit_id, "Invalid channel/chat ID")
            return None
        raise
    except Exception as e:
        logging.error(f"Error in get_msg: {str(e)}", exc_info=True)
        await client.edit_message_text(sender, edit_id, f"An error occurred: {str(e)}")
        return None

async def get_bulk_msg(userbot, client, sender, msg_link, i):
    x = await client.send_message(sender, "Processing!")
    file_name = ''
    await get_msg(userbot, client, sender, x.id, msg_link, i, file_name)
