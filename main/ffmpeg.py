#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
import subprocess
import zipfile
import asyncio
import ffmpeg
import os

#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
def generate_sample_video(input_path, duration, output_path):
    # Get the total duration of the input video using ffprobe
    probe_command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    process = subprocess.Popen(probe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise Exception(f"ffprobe error: {stderr.decode('utf-8')}")
    
    total_duration = float(stdout.decode('utf-8').strip())
    if duration > total_duration:
        raise ValueError("Requested duration is longer than the total duration of the video")

    # Calculate the start time for the sample (middle of the video)
    start_time = (total_duration - duration) / 2

    # Generate the sample video using ffmpeg
    command = [
        'ffmpeg',
        '-ss', str(start_time),
        '-i', input_path,
        '-t', str(duration),
        '-c:v', 'copy',
        '-c:a', 'copy',
        output_path,
        '-y'
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise Exception(f"FFmpeg error: {stderr.decode('utf-8')}")
