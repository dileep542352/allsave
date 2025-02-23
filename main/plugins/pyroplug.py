import asyncio, time, os
from pyrogram.enums import ParseMode, MessageMediaType
from .. import Bot, bot
from main.plugins.progress import progress_for_pyrogram
from main.plugins.helpers import screenshot, video_metadata
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from telethon import events
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.INFO)
logging.getLogger("telethon").setLevel(logging.INFO)

async def get_msg(userbot, client, sender, edit_id, msg_link, i, file_n):
    try:
        msg_id = int(i)
        if msg_id == -1:
            await client.edit_message_text(sender, edit_id, "**Invalid Link!**")
            return None
            
        if 't.me/c/' in msg_link or 't.me/b/' in msg_link:
            try:
                chat = msg_link.split("/")[-2]
                msg = await userbot.get_messages(chat_id=chat, message_ids=msg_id)
                
                if not msg or msg.empty:
                    await client.edit_message_text(sender, edit_id, "Message not found")
                    return None

                if msg.media == MessageMediaType.WEB_PAGE:
                    edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                    await client.send_message(sender, msg.text.markdown if msg.text else "", parse_mode=ParseMode.MARKDOWN)
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

                if not file:
                    await edit.edit("Download failed")
                    return None

                await process_file(client, sender, edit, file, msg, file_n)
                
            except Exception as e:
                await client.edit_message_text(sender, edit_id, f"Error: {str(e)}")
                return None
                
        else:
            edit = await client.edit_message_text(sender, edit_id, "Cloning.")
            chat = msg_link.split("/")[-2]
            try:
                await client.copy_message(sender, chat, msg_id)
                await edit.delete()
            except Exception as e:
                await edit.edit(f"Failed to clone: {str(e)}")
                
    except Exception as e:
        logging.error(f"Error in get_msg: {str(e)}", exc_info=True)
        await client.edit_message_text(sender, edit_id, f"An error occurred: {str(e)}")

async def process_file(client, sender, edit, file, msg, file_n):
    try:
        caption = msg.caption if msg.caption else ""
        
        if str(file).split(".")[-1] in ['mkv', 'mp4', 'webm', 'mpe4', 'mpeg', 'ts', 'avi', 'flv', 'org']:
            if str(file).split(".")[-1] in ['webm', 'mkv', 'mpe4', 'mpeg', 'ts', 'avi', 'flv', 'org']:
                path = str(file).split(".")[0] + ".mp4"
                os.rename(file, path) 
                file = path
                
            data = video_metadata(file)
            duration = data["duration"]
            width = data["width"]
            height = data["height"]

            if file_n:
                path = f'/app/downloads/{file_n}{"." + str(file).split(".")[-1] if "." not in file_n else ""}'
                os.rename(file, path)
                file = path

            thumb_path = f'{sender}.jpg' if os.path.exists(f'{sender}.jpg') else await screenshot(file, duration, sender)

            await client.send_video(
                chat_id=sender,
                video=file,
                caption=caption,
                supports_streaming=True,
                duration=duration,
                height=height,
                width=width,
                thumb=thumb_path,
                progress=progress_for_pyrogram,
                progress_args=(client, '**Uploading...**\n', edit, time.time())
            )

        elif str(file).split(".")[-1] in ['jpg', 'jpeg', 'png', 'webp']:
            if file_n:
                path = f'/app/downloads/{file_n}{"." + str(file).split(".")[-1] if "." not in file_n else ""}'
                os.rename(file, path)
                file = path

            await edit.edit("Uploading photo...")
            await bot.send_file(sender, file, caption=caption)

        else:
            if file_n:
                path = f'/app/downloads/{file_n}{"." + str(file).split(".")[-1] if "." not in file_n else ""}'
                os.rename(file, path)
                file = path

            thumb_path = f'{sender}.jpg' if os.path.exists(f'{sender}.jpg') else None

            await client.send_document(
                sender,
                file,
                caption=caption,
                thumb=thumb_path,
                progress=progress_for_pyrogram,
                progress_args=(client, '**Uploading...**\n', edit, time.time())
            )

    except Exception as e:
        raise e
    finally:
        try:
            os.remove(file)
        except:
            pass
        await edit.delete()

async def get_bulk_msg(userbot, client, sender, msg_link, i):
    x = await client.send_message(sender, "Processing!")
    file_name = ''
    await get_msg(userbot, client, sender, x.id, msg_link, i, file_name)
