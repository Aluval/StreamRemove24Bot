import math, time
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import os
import io
from googleapiclient.http import MediaIoBaseDownload

#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
PROGRESS_BAR = """
╭───[**•PROGRESS BAR•**]───⍟
│
├<b>{5}</b>
│
├<b>📁**PROCESS** : {1} | {2}</b>
│
├<b>🚀**PERCENT** : {0}%</b>
│
├<b>⚡**SPEED** : {3}</b>
│
├<b>⏱️**ETA** : {4}</b>
│
╰─────────────────⍟"""

#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
async def progress_message(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = humanbytes(current / diff) + "/s"
        elapsed_time_ms = round(diff * 1000)
        time_to_completion_ms = round((total - current) / (current / diff)) * 1000
        estimated_total_time_ms = elapsed_time_ms + time_to_completion_ms

        elapsed_time = TimeFormatter(elapsed_time_ms)
        estimated_total_time = TimeFormatter(estimated_total_time_ms)

        progress = "{0}{1}".format(
            ''.join(["■" for i in range(math.floor(percentage / 5))]),
            ''.join(["□" for i in range(20 - math.floor(percentage / 5))])
        )
        tmp = progress + f"\nProgress: {round(percentage, 2)}%\n{humanbytes(current)} of {humanbytes(total)}\nSpeed: {speed}\nETA: {estimated_total_time if estimated_total_time != '' else '0 s'}"

        try:
            await message.edit(
                text=f"{ud_type}\n\n" + PROGRESS_BAR.format(
                    round(percentage, 2),
                    humanbytes(current),
                    humanbytes(total),
                    speed,
                    estimated_total_time if estimated_total_time != '' else '0 s',
                    progress
                ),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌟 Jᴏɪɴ Us 🌟", url="https://t.me/Sunrises24botupdates")]])
            )
        except Exception as e:
            print(f"Error editing message: {e}")


#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "") + \
          ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)


#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24        
# Recursive function to upload file
async def upload_files(bot, chat_id, directory, base_path=""):
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            try:
                await bot.send_document(chat_id, document=item_path, caption=item)
            except Exception as e:
                print(f"Error uploading {item}: {e}")
        elif os.path.isdir(item_path):
            await upload_files(bot, chat_id, item_path, base_path=os.path.join(base_path, item))

async def drive_progress(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    
    # Calculate the percentage and speed
    percentage = current * 100 / total
    speed = humanbytes(current / diff) + "/s"
    # Create a short progress message
    progress = f"{round(percentage, 2)}% - {humanbytes(current)} of {humanbytes(total)} @ {speed}"
    try:
        # Update the bot message with the short progress
        await message.edit(
            text=f"{ud_type}\n\nProgress: {progress}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌟 Jᴏɪɴ Us 🌟", url="https://t.me/Sunrises24botupdates")]])
        )
    except Exception as e:
        print(f"Error editing message: {e}")

async def download_file_from_drive(service, file_id, file_name, message):
    request = service.files().get_media(fileId=file_id)
    file_buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(file_buffer, request)

    done = False
    start_time = time.time()

    while not done:
        status, done = downloader.next_chunk()
        if status:
            current_size = status.resumable_progress
            total_size = status.total_size

            # Update progress message
            await drive_progress(current_size, total_size, "🚀 Downloading from Google Drive... ⚡", message, start_time)

    file_buffer.seek(0)
    with open(file_name, 'wb') as f:
        f.write(file_buffer.read())

    return file_name