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
from config import CAPTION, ADMIN
from main.utils import upload_files, download_file_from_drive
import aiohttp
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup,CallbackQuery
from pyrogram.errors import RPCError, FloodWait
import asyncio
from main.ffmpeg import generate_sample_video
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
import psutil

#varibles for streameremove

selected_streams = set()
downloaded = None
output_filename = None

# Define your constants
FILE_SIZE_LIMIT = 2 * 1024 * 1024 * 1024  # 2 GB Limit (Change if you want)
output_filename = ""


@Client.on_callback_query(filters.regex("^set_sample_video_duration_"))
async def set_sample_video_duration(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    duration_str = callback_query.data.split("_")[-1]
    duration = int(duration_str)
    
    # Save sample video duration to database
    await db.save_sample_video_settings(user_id, duration, "screenshots setting")  # Adjusted the parameter from 'duration' to 'duration_str'
    
    await callback_query.answer(f"Sample video duration set to {duration} seconds.")
    await display_user_settings(client, callback_query.message, edit=True)


@Client.on_callback_query(filters.regex("^sample_video_option$"))
async def sample_video_option(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    current_duration = await db.get_sample_video_settings(user_id)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Sample Video 150s {'✅' if current_duration == 150 else ''}", callback_data="set_sample_video_duration_150")],
        [InlineKeyboardButton(f"Sample Video 120s {'✅' if current_duration == 120 else ''}", callback_data="set_sample_video_duration_120")],
        [InlineKeyboardButton(f"Sample Video 90s {'✅' if current_duration == 90 else ''}", callback_data="set_sample_video_duration_90")],
        [InlineKeyboardButton(f"Sample Video 60s {'✅' if current_duration == 60 else ''}", callback_data="set_sample_video_duration_60")],
        [InlineKeyboardButton(f"Sample Video 30s {'✅' if current_duration == 30 else ''}", callback_data="set_sample_video_duration_30")],
        [InlineKeyboardButton("Back", callback_data="back_to_settings")]
    ])
    
    await callback_query.message.edit_text(f"Sample Video Duration Settings\nCurrent duration: {current_duration}", reply_markup=keyboard)
  

# Callback query handler for returning to user settings
@Client.on_callback_query(filters.regex("^back_to_settings$"))
async def back_to_settings(client, callback_query: CallbackQuery):
    await display_user_settings(client, callback_query.message, edit=True)

@Client.on_message(filters.private & filters.command("usersettings"))
async def display_user_settings(client, msg, edit=False):
    user_id = msg.from_user.id
    
    current_duration = await db.get_sample_video_duration(user_id)
    current_screenshots = await db.get_screenshots_count(user_id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💠", callback_data="sunrises24_bot_updates")],
        [InlineKeyboardButton("Sample Video Settings 🎞️", callback_data="sample_video_option")],
        [InlineKeyboardButton("Screenshots Settings 📸", callback_data="screenshots_option")],
        [InlineKeyboardButton("Thumbnail Settings 📄", callback_data="thumbnail_settings")],       
        [InlineKeyboardButton("💠", callback_data="sunrises24_bot_updates")],
        [InlineKeyboardButton("Close ❌", callback_data="del")]
    ])
    
    if edit:
        await msg.edit_text(f"User Settings\nCurrent sample video duration: {current_duration}\nCurrent screenshots setting: {current_screenshots}", reply_markup=keyboard)
    else:
        await msg.reply(f"User Settings\nCurrent sample video duration: {current_duration}\nCurrent screenshots setting: {current_screenshots}", reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^screenshots_option$"))
async def screenshots_option(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    current_screenshots = await db.get_screenshots_count(user_id)  # Default to 5 if not set
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Screenshots 1 {'✅' if current_screenshots == 1 else ''}", callback_data="set_screenshots_1")],
        [InlineKeyboardButton(f"Screenshots 2 {'✅' if current_screenshots == 2 else ''}", callback_data="set_screenshots_2")],
        [InlineKeyboardButton(f"Screenshots 3 {'✅' if current_screenshots == 3 else ''}", callback_data="set_screenshots_3")],
        [InlineKeyboardButton(f"Screenshots 4 {'✅' if current_screenshots == 4 else ''}", callback_data="set_screenshots_4")],
        [InlineKeyboardButton(f"Screenshots 5 {'✅' if current_screenshots == 5 else ''}", callback_data="set_screenshots_5")],
        [InlineKeyboardButton(f"Screenshots 6 {'✅' if current_screenshots == 6 else ''}", callback_data="set_screenshots_6")],
        [InlineKeyboardButton(f"Screenshots 7 {'✅' if current_screenshots == 7 else ''}", callback_data="set_screenshots_7")],
        [InlineKeyboardButton(f"Screenshots 8 {'✅' if current_screenshots == 8 else ''}", callback_data="set_screenshots_8")],
        [InlineKeyboardButton(f"Screenshots 9 {'✅' if current_screenshots == 9 else ''}", callback_data="set_screenshots_9")],
        [InlineKeyboardButton(f"Screenshots 10 {'✅' if current_screenshots == 10 else ''}", callback_data="set_screenshots_10")],
        [InlineKeyboardButton("Back", callback_data="back_to_settings")]
    ])
    
    await callback_query.message.edit_text(f"Screenshots Settings\nCurrent number: {current_screenshots}", reply_markup=keyboard)
    
@Client.on_callback_query(filters.regex("^set_screenshots_"))
async def set_screenshots(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    num_str = callback_query.data.split("_")[-1]
    num_screenshots = int(num_str)
    
    # Save screenshots count to database
    await db.save_screenshots_count(user_id, num_screenshots)
    
    await callback_query.answer(f"Number of screenshots set to {num_screenshots}.")
    await display_user_settings(client, callback_query.message, edit=True)

@Client.on_callback_query(filters.regex("^thumbnail_settings$"))
async def inline_thumbnail_settings(client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[            
            [InlineKeyboardButton("View Thumbnail", callback_data="view_thumbnail")],
            [InlineKeyboardButton("Delete Thumbnail", callback_data="delete_thumbnail")],
            [InlineKeyboardButton("Back to Settings", callback_data="back_to_settings")]
        ]
    )
    await callback_query.message.edit_text("Thumbnail Settings:", reply_markup=keyboard)

@Client.on_message(filters.private & filters.command("setthumbnail"))
async def set_thumbnail_command(client, message):
    user_id = message.from_user.id

    # Check if thumbnail already exists
    thumbnail_file_id = await db.get_thumbnail(user_id)
    if thumbnail_file_id:
        await message.reply("You already have a permanent thumbnail set. Send a new photo to update it.")
    else:
        await message.reply("Send a photo to set as your permanent thumbnail.")

@Client.on_message(filters.photo & filters.private)
async def set_thumbnail_handler(client, message):
    user_id = message.from_user.id
    photo_file_id = message.photo.file_id

    # Save thumbnail file ID to database
    await db.save_thumbnail(user_id, photo_file_id)
    
    await message.reply("Your permanent thumbnail is updated. If the bot is restarted, the new thumbnail will be preserved.")
    
@Client.on_callback_query(filters.regex("^view_thumbnail$"))
async def view_thumbnail(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    thumbnail_file_id = await db.get_thumbnail(user_id)

    if not thumbnail_file_id:
        await callback_query.message.reply_text("You don't have any thumbnail.")
        return

    try:
        await callback_query.message.reply_photo(photo=thumbnail_file_id, caption="This is your current thumbnail")
    except Exception as e:
        await callback_query.message.reply_text("An error occurred while trying to view your thumbnail.")

@Client.on_callback_query(filters.regex("^delete_thumbnail$"))
async def delete_thumbnail(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    thumbnail_file_id = await db.get_thumbnail(user_id)

    try:
        if thumbnail_file_id:
            await db.delete_thumbnail(user_id)
            await callback_query.message.reply_text("Your thumbnail was removed ❌")
        else:
            await callback_query.message.reply_text("You don't have any thumbnail ‼️")
    except Exception as e:
        await callback_query.message.reply_text("An error occurred while trying to remove your thumbnail. Please try again later.")



@Client.on_callback_query(filters.regex("^preview_gdrive$"))
async def inline_preview_gdrive(bot, callback_query):
    user_id = callback_query.from_user.id
    
    # Retrieve Google Drive folder ID from the database
    gdrive_folder_id = await db.get_gdrive_folder_id(user_id)
    
    if not gdrive_folder_id:
        return await callback_query.message.reply_text(f"Google Drive Folder ID is not set for user `{user_id}`. Use /gdriveid {{your_gdrive_folder_id}} to set it.")
    
    await callback_query.message.reply_text(f"Current Google Drive Folder ID for user `{user_id}`: {gdrive_folder_id}")
    


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
            




async def safe_edit_message(message, text):
    try:
        await message.edit(text)
    except Exception:
        pass

@Client.on_message(filters.command("streamremove") & filters.private)
async def streamremove(bot, msg):
    global selected_streams
    global downloaded
    global output_filename

    reply = msg.reply_to_message
    if not reply:
        return await msg.reply_text(
            "❗ Please reply to a media file with the command\nFormat: `/streamremove -n filename.mkv`"
        )

    if len(msg.command) < 3 or msg.command[1] != "-n":
        return await msg.reply_text(
            "Please provide the filename with the `-n` flag\nFormat: `/streamremove -n filename.mkv`"
        )

    output_filename = " ".join(msg.command[2:]).strip()

    if not output_filename.lower().endswith(('.mkv', '.mp4', '.avi')):
        return await msg.reply_text(
            "Invalid file extension. Please use a valid video file extension (e.g., .mkv, .mp4, .avi)."
        )

    media = reply.document or reply.audio or reply.video
    if not media:
        return await msg.reply_text(
            "❗ Please reply to a valid media file (audio, video, or document) with the command."
        )

    sts = await msg.reply_text("🚀 Downloading media... ⚡")
    c_time = time.time()

    try:
        downloaded = await reply.download(progress=progress_message, progress_args=("🚀 Download Started... ⚡", sts, c_time))
    except Exception as e:
        await sts.edit(f"❌ Error downloading media: {e}")
        return

    # Get the available streams using ffprobe
    ffprobe_cmd = [
        'ffprobe', '-v', 'error', '-show_entries',
        'stream=index:stream_tags=language:stream=codec_type',
        '-of', 'json', downloaded
    ]
    process = await asyncio.create_subprocess_exec(
        *ffprobe_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
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
            audio_video_streams.append(f"{stream_index} 🎵 Audio ({language})")
        elif codec_type == 'subtitle':
            subtitle_streams.append(f"{stream_index} 📝 Subtitle ({language})")
        elif codec_type == 'video':
            audio_video_streams.append(f"{stream_index} 📹 Video")

    # Build the inline keyboard
    buttons = []
    max_len = max(len(audio_video_streams), len(subtitle_streams))
    for i in range(max_len):
        row = []
        if i < len(audio_video_streams):
            row.append(
                InlineKeyboardButton(audio_video_streams[i], callback_data=f"toggle_{audio_video_streams[i].split()[0]}")
            )
        if i < len(subtitle_streams):
            row.append(
                InlineKeyboardButton(subtitle_streams[i], callback_data=f"toggle_{subtitle_streams[i].split()[0]}")
            )
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🔄 Reverse Selection", callback_data="reverse")])
    buttons.append([
        InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        InlineKeyboardButton("✅ Done", callback_data="done")
    ])

    markup = InlineKeyboardMarkup(buttons)
    selected_streams.clear()

    message = await sts.edit("Select the streams you want to remove (you have 60 seconds):", reply_markup=markup)

    await asyncio.sleep(60)

    try:
        await message.edit("🕒 Time's up! Selection process has been canceled.")
        await asyncio.sleep(5)
        await message.delete()
    except:
        pass

    if downloaded and os.path.exists(downloaded):
        os.remove(downloaded)
        
@Client.on_callback_query(filters.regex(r'toggle_\d+|done|cancel|reverse'))
async def callback_query_handler(bot, callback_query: CallbackQuery):
    global selected_streams
    global downloaded
    global output_filename

    data = callback_query.data

    if data == "cancel":
        await callback_query.message.delete()
        if downloaded and os.path.exists(downloaded):
            os.remove(downloaded)
        return

    if data == "reverse":
        buttons = callback_query.message.reply_markup.inline_keyboard
        all_indices = {btn.callback_data.split('_')[1] for row in buttons for btn in row if btn.callback_data.startswith('toggle_')}
        selected_streams.symmetric_difference_update(all_indices)

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

    index = data.split('_')[1]
    if index in selected_streams:
        selected_streams.remove(index)
    else:
        selected_streams.add(index)

    buttons = callback_query.message.reply_markup.inline_keyboard
    for row in buttons:
        for button in row:
            if button.callback_data == f"toggle_{index}":
                if button.text.startswith("✅"):
                    button.text = button.text[2:]
                else:
                    button.text = f"✅ {button.text}"
                break

    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))


async def process_media(bot, callback_query, selected_streams, downloaded, output_filename, sts):
    user_id = callback_query.from_user.id
    output_file = output_filename

    ffmpeg_cmd = ['ffmpeg', '-i', downloaded, '-map', '0']
    for idx in selected_streams:
        ffmpeg_cmd.extend(['-map', f'-0:{idx}'])
    ffmpeg_cmd.extend(['-c', 'copy', output_file, '-y']

    )

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        await safe_edit_message(sts, f"❗ FFmpeg error: {stderr.decode('utf-8')}")
        if downloaded and os.path.exists(downloaded):
            os.remove(downloaded)
        if output_file and os.path.exists(output_file):
            os.remove(output_file)
        return

    # Get thumbnail
    file_thumb = None
    thumb_path = None
    try:
        thumbnail_file_id = await db.get_thumbnail(user_id)
        if thumbnail_file_id:
            thumb_path = await bot.download_media(thumbnail_file_id, file_name=f"thumb_{user_id}.jpg")
    except Exception as e:
        print(f"Thumbnail download error: {e}")
        thumb_path = None

    if thumb_path and os.path.exists(thumb_path):
        file_thumb = thumb_path
    else:
        file_thumb = None

    filesize = os.path.getsize(output_file)
    filesize_human = humanbytes(filesize)
    caption_text = f"**Processed File:** {output_filename}\n\n🌟 **Size:** {filesize_human}"

    await safe_edit_message(sts, "💠 Uploading... ⚡")
    c_time = time.time()

    if filesize > FILE_SIZE_LIMIT:
        file_link = await upload_to_google_drive(output_file, output_filename, sts)
        button = [[InlineKeyboardButton("☁️ CloudUrl ☁️", url=file_link)]]
        await bot.send_message(
            chat_id=user_id,
            text=f"**✅ Uploaded to GDrive:** [View File]({file_link})",
            reply_markup=InlineKeyboardMarkup(button)
        )
    else:
        try:
            await bot.send_document(
                chat_id=user_id,
                document=output_file,
                thumb=file_thumb,
                caption=caption_text,
                progress=progress_message,
                progress_args=("💠 Upload Started... ⚡", sts, c_time)
            )
        except Exception as e:
            await safe_edit_message(sts, f"❗ Upload Error: {e}")

    await bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"✅ File `{output_filename}` processed and sent to {callback_query.from_user.mention}."
    )

    # Clean up
    if downloaded and os.path.exists(downloaded):
        os.remove(downloaded)
    if output_file and os.path.exists(output_file):
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
    
@Client.on_message(filters.command("screenshots") & filters.private)
async def screenshots_command(client, message: Message):
    user_id = message.from_user.id

    # Fetch user settings for screenshots count
    num_screenshots = await db.get_screenshots_count(user_id)
    if not num_screenshots:
        num_screenshots = 5  # Default to 5 if not set

    if not message.reply_to_message:
        return await message.reply_text("Please reply to a valid video file or document.")

    media = message.reply_to_message.video or message.reply_to_message.document
    if not media:
        return await message.reply_text("Please reply to a valid video file.")

    sts = await message.reply_text("🚀 Downloading media... ⚡")
    try:
        input_path = await client.download_media(media)
    except Exception as e:
        await sts.edit(f"Error downloading media: {e}")
        return

    if not os.path.exists(input_path):
        await sts.edit("Error: The downloaded file does not exist.")
        return

    try:
        await sts.edit("🚀 Reading video duration... ⚡")
        command = ['ffprobe', '-i', input_path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
        duration_output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        duration = float(duration_output.decode('utf-8').strip())
    except subprocess.CalledProcessError as e:
        await sts.edit(f"Error reading video duration: {e.output.decode('utf-8')}")
        os.remove(input_path)
        return
    except ValueError:
        await sts.edit("Error reading video duration: Unable to convert duration to float.")
        os.remove(input_path)
        return

    interval = duration / num_screenshots

    await sts.edit(f"🚀 Generating {num_screenshots} screenshots... ⚡")
    screenshot_paths = []
    for i in range(num_screenshots):
        time_position = interval * i
        screenshot_path = f"screenshot_{user_id}_{i}.jpg"

        command = ['ffmpeg', '-ss', str(time_position), '-i', input_path, '-vframes', '1', '-y', screenshot_path]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            await sts.edit(f"Error generating screenshot {i+1}: {stderr.decode('utf-8')}")
            for path in screenshot_paths:
                os.remove(path)
            os.remove(input_path)
            return

        screenshot_paths.append(screenshot_path)

        # Upload screenshot to user's PM
        try:
            await client.send_photo(chat_id=user_id, photo=screenshot_path)
        except Exception as e:
            await sts.edit(f"Error uploading screenshot {i+1}: {e}")
            os.remove(screenshot_path)

        os.remove(screenshot_path)  # Remove local screenshot after uploading

    # Save screenshot paths to database
    await db.save_screenshot_paths(user_id, screenshot_paths)

    os.remove(input_path)  # Remove downloaded media file

    # Send notification in group chat
    try:
        await message.reply_text("📸 Screenshots have been sent to your PM.")
    except Exception as e:
        print(f"Failed to send notification: {e}")

    # Cleanup: Delete screenshot paths from database after sending
    await db.delete_screenshot_paths(user_id)

    await sts.delete()  # Delete the status message after completion


@Client.on_message(filters.command("samplevideo") & filters.private)
async def sample_video(bot, msg):
    user_id = msg.from_user.id

    # Fetch user settings
    sample_video_duration = await db.get_sample_video_duration(user_id)

    if sample_video_duration is None:
        return await msg.reply_text("Please set a valid sample video duration using /usersettings.")

    if not msg.reply_to_message:
        return await msg.reply_text("Please reply to a valid video file or document.")

    media = msg.reply_to_message.video or msg.reply_to_message.document
    if not media:
        return await msg.reply_text("Please reply to a valid video file or document.")

    sts = await msg.reply_text("🚀 Downloading media... ⚡")
    c_time = time.time()
    try:
        input_path = await bot.download_media(media, progress=progress_message, progress_args=("🚀 Downloading media... ⚡️", sts, c_time))
    except Exception as e:
        await sts.edit(f"Error downloading media: {e}")
        return

    output_file = f"sample_video_{sample_video_duration}s.mp4"

    await sts.edit("🚀 Processing sample video... ⚡")
    try:
        generate_sample_video(input_path, sample_video_duration, output_file)
    except Exception as e:
        await sts.edit(f"Error generating sample video: {e}")
        os.remove(input_path)
        return

    filesize = os.path.getsize(output_file)
    filesize_human = humanbytes(filesize)
    cap = f"{os.path.basename(output_file)}\n\n🌟 Size: {filesize_human}"

    await sts.edit("💠 Uploading sample video to your PM... ⚡")
    c_time = time.time()
    try:
        await bot.send_document(
            user_id, 
            document=output_file, 
            caption=cap, 
            progress=progress_message, 
            progress_args=("💠 Upload Started... ⚡️", sts, c_time)
        )
        # Save sample video settings to database
        await db.save_sample_video_settings(user_id, sample_video_duration, "Not set")

        # Send notification about the file upload
        await msg.reply_text(f"File Sample Video has been uploaded to your PM. Check your PM of the bot ✅ .")

    except Exception as e:
        await sts.edit(f"Error uploading sample video: {e}")
        return

    os.remove(input_path)
    os.remove(output_file)
    await sts.delete()


@Client.on_message(filters.command("ban") & filters.user(ADMIN))
async def ban_user(bot, msg: Message):
    try:
        user_id = int(msg.text.split()[1])
        # Ban user in the database
        await db.ban_user(user_id)
        # Ban user from the chat
        await bot.ban_chat_member(chat_id=msg.chat.id, user_id=user_id)
        await msg.reply_text(f"User {user_id} has been banned.")
    except PyMongoError as e:
        await msg.reply_text(f"Database error occurred: {e}")
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await msg.reply_text(f"Flood wait error: Please try again later.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {e}")

@Client.on_message(filters.command("unban") & filters.user(ADMIN))
async def unban_user(bot, msg: Message):
    try:
        user_id = int(msg.text.split()[1])
        # Unban user in the database
        await db.unban_user(user_id)
        # Unban user from the chat
        await bot.unban_chat_member(chat_id=msg.chat.id, user_id=user_id)
        await msg.reply_text(f"User {user_id} has been unbanned.")
    except PyMongoError as e:
        await msg.reply_text(f"Database error occurred: {e}")
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await msg.reply_text(f"Flood wait error: Please try again later.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {e}")

@Client.on_message(filters.command("users") & filters.user(ADMIN))
async def count_users(bot, msg):
    try:
        total_users = await db.count_users()
        banned_users = await db.count_banned_users()

        response = (
            f"**User Statistics:**\n"
            f"Total Active Users: {total_users}\n"
            f"Banned Users: {banned_users}"
        )
        await msg.reply_text(response)
    except PyMongoError as e:
        await msg.reply_text(f"Database error occurred while counting users: {e}")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {e}")

@Client.on_message(filters.command("stats") & filters.chat(GROUP))        
async def stats_command(_, msg):
    uptime = datetime.datetime.now() - START_TIME
    uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

    total_space = psutil.disk_usage('/').total / (1024 ** 3)
    used_space = psutil.disk_usage('/').used / (1024 ** 3)
    free_space = psutil.disk_usage('/').free / (1024 ** 3)

    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    stats_message = (
        f"📊 **Server Stats** 📊\n\n"
        f"⏳ **Uptime:** `{uptime_str}`\n"
        f"💾 **Total Space:** `{total_space:.2f} GB`\n"
        f"📂 **Used Space:** `{used_space:.2f} GB` ({used_space / total_space * 100:.1f}%)\n"
        f"📁 **Free Space:** `{free_space:.2f} GB`\n"
        f"⚙️ **CPU Usage:** `{cpu_usage:.1f}%`\n"
        f"💻 **RAM Usage:** `{ram_usage:.1f}%`\n"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats")]
        ]
    )

    await msg.reply_text(stats_message, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^refresh_stats$"))
async def refresh_stats_callback(_, callback_query):
    # Refresh stats
    uptime = datetime.datetime.now() - START_TIME
    uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))

    total_space = psutil.disk_usage('/').total / (1024 ** 3)
    used_space = psutil.disk_usage('/').used / (1024 ** 3)
    free_space = psutil.disk_usage('/').free / (1024 ** 3)

    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    stats_message = (
        f"📊 **Server Stats** 📊\n\n"
        f"⏳ **Uptime:** `{uptime_str}`\n"
        f"💾 **Total Space:** `{total_space:.2f} GB`\n"
        f"📂 **Used Space:** `{used_space:.2f} GB` ({used_space / total_space * 100:.1f}%)\n"
        f"📁 **Free Space:** `{free_space:.2f} GB`\n"
        f"⚙️ **CPU Usage:** `{cpu_usage:.1f}%`\n"
        f"💻 **RAM Usage:** `{ram_usage:.1f}%`\n"
    )

    await callback_query.message.edit_text(stats_message, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats")]
        ]
    ))


@Client.on_message(filters.command("clear") & filters.user(ADMIN))
async def clear_database_handler(client: Client, msg: Message):
    try:
        await db.clear_database()
        await msg.reply_text("Database has been cleared✅.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {e}")

@Client.on_message(filters.command("broadcast") & filters.user(ADMIN))
async def broadcast(bot, msg: Message):
    if not msg.reply_to_message:
        await msg.reply_text("Please reply to a message to broadcast it.")
        return

    broadcast_message = msg.reply_to_message

    # Fetch all user IDs
    user_ids = await db.get_all_user_ids()

    sent_count = 0
    failed_count = 0
    log_entries = []

    for user_id in user_ids:
        try:
            await broadcast_message.copy(chat_id=user_id)
            sent_count += 1
            log_entries.append(f"Sent to {user_id}")
        except Exception as e:
            failed_count += 1
            log_entries.append(f"Failed to send to {user_id}: {e}")

        await asyncio.sleep(0.5)  # To avoid hitting rate limits

    # Write log entries to a text file
    log_content = "\n".join(log_entries)
    with open("broadcast_log.txt", "w") as log_file:
        log_file.write(log_content)

    # Send summary to admin
    await msg.reply_text(f"Broadcast completed: {sent_count} sent, {failed_count} failed.")
    await msg.reply_document('broadcast_log.txt')

