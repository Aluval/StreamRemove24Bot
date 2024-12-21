

#handler is streamremove
@Client.on_message(filters.command("streamremove") & filters.chat(GROUP))
async def streamremove(bot, msg):
    global STREAMREMOVE_ENABLED
    global selected_streams
    global downloaded
    global output_filename

    if not STREAMREMOVE_ENABLED:
        return await msg.reply_text("🚫 The streamremove feature is currently disabled.")

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


