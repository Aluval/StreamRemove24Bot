#TG : @Sunrises_24
#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
import subprocess
import os, json
import time
import ffmpeg
from pyrogram.types import Message
from pyrogram.types import Document, Video
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import MessageNotModified
from main.utils import progress_message, humanbytes
from config import CAPTION
from main.utils import upload_files, download_file_from_drive
import aiohttp
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup,CallbackQuery
from pyrogram.errors import RPCError, FloodWait
import asyncio
from googleapiclient.http import MediaFileUpload
from main.gdrive import upload_to_google_drive, extract_id_from_url, copy_file, get_files_in_folder, drive_service
from googleapiclient.errors import HttpError
import datetime
from datetime import timedelta
from os import execl as osexecl
from sys import executable
from config import *
from Database.database import db
from pymongo.errors import PyMongoError

#varibles for streameremove
selected_streams = set()
downloaded = None

@Client.on_message(filters.private & filters.command("usersettings"))
async def display_user_settings(client, msg, edit=False):
    user_id = msg.from_user.id
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💠", callback_data="sunrises24_bot_updates")],
        [InlineKeyboardButton("View Google Drive Folder ID 📂", callback_data="preview_gdrive")],
        [InlineKeyboardButton("💠", callback_data="sunrises24_bot_updates")],
        [InlineKeyboardButton("Close ❌", callback_data="del")]
    ])
    
@Client.on_message(filters.private & filters.command("mirror"))
async def mirror_to_google_drive(bot, msg: Message):
   
    user_id = msg.from_user.id
    
    # Retrieve the user's Google Drive folder ID
    gdrive_folder_id = await db.get_gdrive_folder_id(user_id)
    
    if not gdrive_folder_id:
        return await msg.reply_text("Google Drive folder ID is not set. Please use the /gdriveid command to set it.")

    reply = msg.reply_to_message
    if len(msg.command) < 2 or not reply:
        return await msg.reply_text("Please reply to a file with the new filename and extension.")

    media = reply.document or reply.audio or reply.video
    if not media:
        return await msg.reply_text("Please reply to a file with the new filename and extension.")

    new_name = msg.text.split(" ", 1)[1]

    try:
        # Show progress message for downloading
        sts = await msg.reply_text("🚀 Downloading...")
        
        # Download the file
        downloaded_file = await bot.download_media(message=reply, file_name=new_name, progress=progress_message, progress_args=("Downloading", sts, time.time()))
        filesize = os.path.getsize(downloaded_file)
        
        # Once downloaded, update the message to indicate uploading
        await sts.edit("💠 Uploading...")
        
        start_time = time.time()

        # Upload file to Google Drive
        file_metadata = {'name': new_name, 'parents': [gdrive_folder_id]}
        media = MediaFileUpload(downloaded_file, resumable=True)

        # Upload with progress monitoring
        request = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink')
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                current_progress = status.progress() * 100
                await progress_message(current_progress, 100, "Uploading to Google Drive", sts, start_time)

        file_id = response.get('id')
        file_link = response.get('webViewLink')

        # Prepare caption for the uploaded file
        if CAPTION:
            caption_text = CAPTION.format(file_name=new_name, file_size=humanbytes(filesize))
        else:
            caption_text = f"Uploaded File: {new_name}\nSize: {humanbytes(filesize)}"

        # Send the Google Drive link to the user
        button = [
            [InlineKeyboardButton("☁️ CloudUrl ☁️", url=f"{file_link}")]
        ]
        await msg.reply_text(
            f"File successfully mirrored and uploaded to Google Drive!\n\n"
            f"Google Drive Link: [View File]({file_link})\n\n"
            f"Uploaded File: {new_name}\n"
            f"Size: {humanbytes(filesize)}",
            reply_markup=InlineKeyboardMarkup(button)
        )
        os.remove(downloaded_file)
        await sts.delete()

    except Exception as e:
        await sts.edit(f"Error: {e}")
            
#handler is streamremove
@Client.on_message(filters.command("streamremove") & filters.private)
async def streamremove(bot, msg):
    global selected_streams
    global downloaded
    global output_filename

    reply = msg.reply_to_message
    if not reply:
        return await msg.reply_text("❗ Please reply to a media file with the command\nFormat: `/streamremove -n filename.mkv`")

    if len(msg.command) < 3 or msg.command[1] != "-n":
        return await msg.reply_text("Please provide the filename with the `-n` flag\nFormat: `/streamremove -n filename.mkv`")

    output_filename = " ".join(msg.command[2:]).strip()

    if not output_filename.lower().endswith(('.mkv', '.mp4', '.avi')):
        return await msg.reply_text("Invalid file extension. Please use a valid video file extension (e.g., .mkv, .mp4, .avi).")

    media = reply.document or reply.audio or reply.video
    if not media:
        return await msg.reply_text("❗ Please reply to a valid media file (audio, video, or document) with the command.")

    sts = await msg.reply_text("🚀 Downloading media... ⚡")
    c_time = time.time()
    try:
        downloaded = await reply.download(progress=progress_message, progress_args=("🚀 Download Started... ⚡️", sts, c_time))
    except Exception as e:
        await sts.edit(f"❌ Error downloading media: {e}")
        return

    # Get the available streams
    ffprobe_cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'stream=index:stream_tags=language:stream=codec_type', '-of', 'json', downloaded
    ]
    process = await asyncio.create_subprocess_exec(*ffprobe_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        await sts.edit(f"❗ FFprobe error: {stderr.decode('utf-8')}")
        os.remove(downloaded)
        return

    streams = json.loads(stdout.decode('utf-8')).get('streams', [])
    audio_video_streams = []
    subtitle_streams = []

    for stream in streams:
        stream_index = stream['index']
        language = stream.get('tags', {}).get('language', 'unknown')
        codec_type = stream['codec_type']

        if codec_type == 'audio':
            if language == 'tel':
                audio_video_streams.append(f"{stream_index} 🎵 Telugu Audio")
            elif language == 'tam':
                audio_video_streams.append(f"{stream_index} 🎵 Tamil Audio")
            elif language == 'hin':
                audio_video_streams.append(f"{stream_index} 🎵 Hindi Audio")
            else:
                audio_video_streams.append(f"{stream_index} 🎵 Audio - {language}")
        elif codec_type == 'subtitle':
            if language == 'eng':
                subtitle_streams.append(f"{stream_index} 📝 English Subtitle")
            else:
                subtitle_streams.append(f"{stream_index} 📝 {language} - Subtitle")
        elif codec_type == 'video':
            audio_video_streams.append(f"{stream_index} 📹 Video")

    # Build the inline keyboard with available streams
    buttons = []
    max_len = max(len(audio_video_streams), len(subtitle_streams))
    for i in range(max_len):
        row = []
        if i < len(audio_video_streams):
            row.append(InlineKeyboardButton(f"{audio_video_streams[i]}", callback_data=f"toggle_{audio_video_streams[i].split()[0]}"))
        if i < len(subtitle_streams):
            row.append(InlineKeyboardButton(f"{subtitle_streams[i]}", callback_data=f"toggle_{subtitle_streams[i].split()[0]}"))
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🔄 Reverse Selection", callback_data="reverse")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel"), InlineKeyboardButton("✅ Done", callback_data="done")])
    markup = InlineKeyboardMarkup(buttons)

    selected_streams.clear()
    start_time = time.time()
    message = await sts.edit("Select the streams you want to remove (you have 60 seconds):", reply_markup=markup)

    # Wait for 60 seconds
    await asyncio.sleep(60)

    if time.time() - start_time < 60:
        # If the user has not interacted within 60 seconds, cancel the process
        if message:
            await message.edit("🕒 Time's up! Selection process has been canceled.")
            await asyncio.sleep(5)  # Keep the message visible for a short time before deleting
            await message.delete()
            if downloaded:
                os.remove(downloaded)

@Client.on_callback_query(filters.regex(r'toggle_\d+|done|cancel|reverse'))
async def callback_query_handler(bot, callback_query: CallbackQuery):
    global selected_streams
    global downloaded
    global output_filename
    data = callback_query.data

    # Check if the user who initiated the command matches the callback query user
    if callback_query.from_user.id != callback_query.message.reply_to_message.from_user.id:
        return

    if data == "cancel":
        await callback_query.message.delete()
        if downloaded:
            os.remove(downloaded)
        return

    if data == "reverse":
        buttons = callback_query.message.reply_markup.inline_keyboard
        all_indices = {btn.callback_data.split('_')[1] for row in buttons for btn in row if btn.callback_data.startswith('toggle_')}
        selected_streams.symmetric_difference_update(all_indices)

        # Update button text
        for row in buttons:
            for button in row:
                if button.callback_data.startswith("toggle_"):
                    index = button.callback_data.split('_')[1]
                    if index in selected_streams:
                        button.text = f"✅ {button.text.lstrip('✅').strip()}"
                    else:
                        button.text = button.text.lstrip('✅').strip()

        await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "done":
        sts = await callback_query.message.edit_text("💠 Removing selected streams... ⚡")
        await process_media(bot, callback_query, selected_streams, downloaded, output_filename, sts)
        return

    # Toggle selection state
    index = data.split('_')[1]
    if index in selected_streams:
        selected_streams.remove(index)
    else:
        selected_streams.add(index)

    # Update buttons to reflect selection
    buttons = callback_query.message.reply_markup.inline_keyboard
    for row in buttons:
        for button in row:
            if button.callback_data == f"toggle_{index}":
                if button.text.startswith("✅"):
                    button.text = button.text[2:]  # Remove the checkmark
                else:
                    button.text = f"✅ {button.text}"  # Add the checkmark
                break

    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))



# Process media function
async def process_media(bot, callback_query, selected_streams, downloaded, output_filename, sts):
    user_id = callback_query.from_user.id
    original_message = callback_query.message.reply_to_message
    output_file = output_filename

    # Construct FFmpeg command to process media
    ffmpeg_cmd = ['ffmpeg', '-i', downloaded, '-map', '0']
    for idx in selected_streams:
        ffmpeg_cmd.extend(['-map', f'-0:{idx}'])
    ffmpeg_cmd.extend(['-c', 'copy', output_file, '-y'])

    # Execute FFmpeg command
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd, 
        stdout=asyncio.subprocess.PIPE, 
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        await safe_edit_message(sts, f"❗ FFmpeg error: {stderr.decode('utf-8')}")
        os.remove(downloaded)
        if os.path.exists(output_file):
            os.remove(output_file)
        return

    # Retrieve thumbnail from the database
    thumbnail_file_id = await db.get_thumbnail(user_id)
    file_thumb = None
    if thumbnail_file_id:
        try:
            file_thumb = await bot.download_media(thumbnail_file_id)
        except Exception:
            pass
    else:
        if hasattr(original_message, 'thumbs') and original_message.thumbs:
            try:
                file_thumb = await bot.download_media(original_message.thumbs[0].file_id)
            except Exception as e:
                file_thumb = None

    filesize = os.path.getsize(output_file)
    filesize_human = humanbytes(filesize)
    cap = f"{output_filename}\n\n🌟 Size: {filesize_human}"

    await safe_edit_message(sts, "💠 Uploading... ⚡")
    c_time = time.time()

    if filesize > FILE_SIZE_LIMIT:
        file_link = await upload_to_google_drive(output_file, output_filename, sts)
        button = [[InlineKeyboardButton("☁️ CloudUrl ☁️", url=file_link)]]
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"**File successfully stream removed and uploaded to Google Drive!**\n\n"
                f"**Google Drive Link**: [View File]({file_link})\n\n"
                f"**Uploaded File**: {output_filename}\n"
                f"**Request User:** {callback_query.from_user.mention}\n\n"
                f"**Size**: {filesize_human}"
            ),
            reply_markup=InlineKeyboardMarkup(button)
        )
    else:
        try:
            await bot.send_document(
                chat_id=user_id,
                document=output_file,
                thumb=file_thumb,
                caption=cap,
                progress=progress_message,
                progress_args=("💠 Upload Started... ⚡", sts, c_time)
            )
        except Exception as e:
            await safe_edit_message(sts, f"Error: {e}")

    # Send a message to the user after the file is sent to their PM
    group_message_text = (
        f"┏📥 **File Name:** {output_filename}\n"
        f"┠💾 **Size:** {filesize_human}\n"
        f"┠♻️ **Mode:** Stream Remove\n"                
        f"┗🚹 **Request User:** {callback_query.from_user.mention}\n\n"
        f"❄ **File has been sent in Bot PM!**"
    )
    await bot.send_message(
        chat_id=LOG_CHANNEL,  # Send the group message to the user
        text=group_message_text
    )

    os.remove(downloaded)
    os.remove(output_file)
    if file_thumb and os.path.exists(file_thumb):
        os.remove(file_thumb)
    await sts.delete()


# Command handler for /list
@Client.on_message(filters.private & filters.command("list"))
async def list_files(bot, msg: Message):
    user_id = msg.from_user.id

    # Retrieve the user's Google Drive folder ID from database
    gdrive_folder_id = await db.get_gdrive_folder_id(user_id)

    if not gdrive_folder_id:
        return await msg.reply_text("Google Drive folder ID is not set. Please use the /gdriveid command to set it.")

    sts = await msg.reply_text("Fetching File List...🔎")

    try:
        files = get_files_in_folder(gdrive_folder_id)
        if not files:
            return await sts.edit("No files found in the specified folder.")

        # Categorize files
        file_types = {'Images': [], 'Movies': [], 'Audios': [], 'Archives': [], 'Others': []}
        for file in files:
            mime_type = file['mimeType']
            file_name = file['name'].lower()
            if mime_type.startswith('image/'):
                file_types['Images'].append(file)
            elif mime_type.startswith('video/') or file_name.endswith(('.mkv', '.mp4')):
                file_types['Movies'].append(file)
            elif mime_type.startswith('audio/') or file_name.endswith(('.aac', '.eac3', '.mp3', '.opus', '.eac')):
                file_types['Audios'].append(file)
            elif file_name.endswith(('.zip', '.rar')):
                file_types['Archives'].append(file)
            else:
                file_types['Others'].append(file)

        # Create inline buttons for each category with emojis
        buttons = []
        for category, items in file_types.items():
            if items:
                if category == 'Images':
                    emoji = '🖼️'
                elif category == 'Movies':
                    emoji = '🎞️'
                elif category == 'Audios':
                    emoji = '🔊'
                elif category == 'Archives':
                    emoji = '📦'
                else:
                    emoji = '📁'

                buttons.append([InlineKeyboardButton(f"{emoji} {category}", callback_data=f"{category}")])
                for file in sorted(items, key=lambda x: x['name']):
                    file_link = f"https://drive.google.com/file/d/{file['id']}/view"
                    buttons.append([InlineKeyboardButton(file['name'], url=file_link)])

        await sts.edit(
            "Files In The Specified Folder 📁:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except HttpError as error:
        await sts.edit(f"An error occurred: {error}")
    except Exception as e:
        await sts.edit(f"Error: {e}")

#cleam command
@Client.on_message(filters.private & filters.command("clean"))
async def clean_files(bot, msg: Message):
    user_id = msg.from_user.id

    # Retrieve the user's Google Drive folder ID from database
    gdrive_folder_id = await db.get_gdrive_folder_id(user_id)

    if not gdrive_folder_id:
        return await msg.reply_text("Google Drive folder ID is not set. Please use the /gdriveid command to set it.")

    try:
        # Check if the command is followed by a file name or a direct link
        command_parts = msg.text.split(maxsplit=1)
        if len(command_parts) < 2:
            return await msg.reply_text("Please provide a file name or direct link to delete.")

        query_or_link = command_parts[1].strip()

        # If the query_or_link starts with 'http', treat it as a direct link
        if query_or_link.startswith("http"):
            # Extract file ID from the direct link
            file_id = extract_id_from_url(query_or_link)
            if not file_id:
                return await msg.reply_text("Invalid Google Drive file link. Please provide a valid direct link.")

            # Delete the file by its ID
            drive_service.files().delete(fileId=file_id).execute()
            await msg.reply_text(f"Deleted File with ID '{file_id}' Successfully ✅.")

        else:
            # Treat it as a file name and delete files by name in the specified folder
            file_name = query_or_link

            # Define query to find files by name in the specified folder
            query = f"'{gdrive_folder_id}' in parents and trashed=false and name='{file_name}'"

            # Execute the query to find matching files
            response = drive_service.files().list(q=query, fields='files(id, name)').execute()
            files = response.get('files', [])

            if not files:
                return await msg.reply_text(f"No files found with the name '{file_name}' in the specified folder.")

            # Delete each found file
            for file in files:
                drive_service.files().delete(fileId=file['id']).execute()
                await msg.reply_text(f"Deleted File '{file['name']}' Successfully ✅.")

    except HttpError as error:
        await msg.reply_text(f"An error occurred: {error}")
    except Exception as e:
        await msg.reply_text(f"An unexpected error occurred: {e}")
        
@Client.on_message(filters.command("clear") & filters.user(ADMIN))
async def clear_database_handler(client: Client, msg: Message):
    try:
        await db.clear_database()
        await msg.reply_text("Database has been cleared✅.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {e}")

#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
#Ping
@Client.on_message(filters.command("ping"))
async def ping(bot, msg):
    start_t = time.time()
    rm = await msg.reply_text("Checking")
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await rm.edit(f"Pong!📍\n{time_taken_s:.3f} ms")

#safe edit message 
async def safe_edit_message(message, new_text):
    try:
        if message.text != new_text:
            await message.edit(new_text[:4096])  # Ensure text does not exceed 4096 characters
    except Exception as e:
        print(f"Failed to edit message: {e}")


#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
@Client.on_callback_query(filters.regex("del"))
async def closed(bot, msg):
    try:
        await msg.message.delete()
    except:
        return

    # Callback query handler for the "sunrises24_bot_updates" button
@Client.on_callback_query(filters.regex("^sunrises24_bot_updates$"))
async def sunrises24_bot_updates_callback(_, callback_query):
    await callback_query.answer("MADE BY @SUNRISES24BOTUPDATES ❤️", show_alert=True)    
    
@Client.on_message(filters.private & filters.command("gdriveid"))
async def setup_gdrive_id(bot, msg: Message):
    user_id = msg.from_user.id
    args = msg.text.split(" ", 1)
    if len(args) != 2:
        return await msg.reply_text("Usage: /gdriveid {your_gdrive_folder_id}")
    
    gdrive_folder_id = args[1].strip()
    
    # Save Google Drive folder ID to the database
    await db.save_gdrive_folder_id(user_id, gdrive_folder_id)
    
    await msg.reply_text(f"Google Drive folder ID set to: {gdrive_folder_id} for user `{user_id}`\n\nGoogle Drive folder ID set successfully✅!")


@Client.on_callback_query(filters.regex("^preview_gdrive$"))
async def inline_preview_gdrive(bot, callback_query):
    user_id = callback_query.from_user.id
    
    # Retrieve Google Drive folder ID from the database
    gdrive_folder_id = await db.get_gdrive_folder_id(user_id)
    
    if not gdrive_folder_id:
        return await callback_query.message.reply_text(f"Google Drive Folder ID is not set for user `{user_id}`. Use /gdriveid {{your_gdrive_folder_id}} to set it.")
    
    await callback_query.message.reply_text(f"Current Google Drive Folder ID for user `{user_id}`: {gdrive_folder_id}")
    

