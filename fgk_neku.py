import discord
from discord.ext import commands
import json
import os
import requests
import base64
import random
import io
import tempfile
import subprocess
from nodejs import node, npm
from datetime import timedelta
import numpy as np
import librosa
import cv2
import os
import asyncio

class FGKBot(commands.Cog):
    def __init__(self, bot):
        self.BOT_CONFIG = self.load_json("config/bot_config.json")
        self.inworld_key = self.BOT_CONFIG["INWORLD-KEY"]
        self.inworld_secret = self.BOT_CONFIG["INWORLD-SECRET"]
        self.inworld_scene = self.BOT_CONFIG["INWORLD-SCENE"]
        self.bot = bot
        
        # Initialize the grid
        self.rows = 3
        self.grid = [[], [], []]

        # Iterate over the videos and extract frames
        for i in range(self.rows):
            video_path = f"vids/{i}.mp4"
                
            # Skip if video file doesn't exist
            if not os.path.isfile(video_path):
                print(f"Warning: {video_path} not found. Skipping.")
                continue

            video = cv2.VideoCapture(video_path)

            while video.isOpened():
                ret, frame = video.read()
                if not ret:
                    break
                self.grid[i].append(frame)

            video.release()

        print("Frames loaded")

    async def audio_analysis(self, filepath):
        # Desired frame rate
        fps = 16
        frame_length = 1 / fps  # Frame length in seconds

        # Load the audio file
        y, sr = librosa.load(filepath)

        # Number of samples per frame
        frame_samples = int(sr * frame_length)

        # Split audio into frames and initialize results
        frames = [y[i:i + frame_samples] for i in range(0, len(y), frame_samples)]
        volume_class = []

        for frame in frames:
            # Volume (RMS energy) analysis
            rms = np.sqrt(np.mean(frame**2))
            volume_class.append(0 if rms < 0.1 else 1 if rms < 0.125 else 2) 

        # Return paired results
        return volume_class

    async def create_grid_video(self, frame_sequence, output_file="crockpot/output_video.mp4"):
        # Define the codec and create a VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_video = cv2.VideoWriter(output_file, fourcc, 16.0, (512, 512))  # assumes frames are 512x512

        # Iterate over the frame_sequence
        for i in range(len(frame_sequence)):
            A = frame_sequence[i]
            frame = self.grid[A][i%32]

            output_video.write(frame)

        # Release everything after the job is done
        output_video.release()
        cv2.destroyAllWindows()

        # Combine video and audio using FFmpeg
        command = [
            'ffmpeg',
            '-i', output_file,
            '-i', 'crockpot/merged_sox.mp3',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            'crockpot/output_with_audio.mp4'
        ]
        subprocess.run(command)

    def concatenate_texts(self, objects_list):
        concatenated_text = ""
        for obj in objects_list:
            concatenated_text += obj["text"]
        return concatenated_text

    async def merge_base64_mp3s_sox(self, mp3_dict_list, output_file, srt_file_path):
        # Create a temporary directory to store the decoded MP3 files
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Decode each Base64 string to binary MP3 data and save as a file
            mp3_file_paths = []
            srt_entries = []
            current_time = timedelta()
    
            for i, mp3_dict in enumerate(mp3_dict_list):
                mp3_data = base64.b64decode(mp3_dict['audio'])
                mp3_file_path = os.path.join(tmp_dir, f"segment_{i}.mp3")
                with open(mp3_file_path, 'wb') as f:
                    f.write(mp3_data)
                mp3_file_paths.append(mp3_file_path)
    
                # Get the duration using ffprobe
                duration = self.get_duration_ffprobe(mp3_file_path)
    
                # Write SRT entries
                end_time = current_time + timedelta(seconds=duration)
                srt_entries.append((i + 1, current_time, end_time, mp3_dict["text"]))
                current_time = end_time
    
            # Call SoX to concatenate the MP3 files
            sox_cmd = [
                "sox",
                *mp3_file_paths,  # List of input MP3 files
                output_file,
            ]
            subprocess.run(sox_cmd, check=True)
    
            # Write the SRT file
            self.write_srt_file(srt_entries, srt_file_path)
    
    def get_duration_ffprobe(self, mp3_file_path):
        ffprobe_cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            mp3_file_path,
        ]
    
        ffprobe_output = subprocess.check_output(ffprobe_cmd)
        ffprobe_data = json.loads(ffprobe_output)
        duration = float(ffprobe_data["format"]["duration"])
        return duration

    def format_timedelta(self, td):
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def write_srt_file(self, srt_entries, srt_file_path):
        with open(srt_file_path, 'w', encoding='utf-8') as f:
            for entry in srt_entries:
                f.write(f"{entry[0]}\n")
                f.write(f"{self.format_timedelta(entry[1])} --> {self.format_timedelta(entry[2])}\n")
                f.write(f"{entry[3]}\n\n")
                
    def chat_app(self, query, user_name, user_channel, user_id):
        node_process = node.Popen(["bin/iw.js", 
                    self.inworld_key, 
                    self.inworld_secret,
                    self.inworld_scene,
                    query,
                    user_name,
                    user_channel,
                    user_id],
        stdout=subprocess.PIPE)
        output, error = node_process.communicate()

        return output.decode('utf-8')
    

    def clean_up(self):
        os.system("rm crockpot/*")

    def load_json(self, file_name):
        with open(file_name) as json_file:
            data = json.load(json_file)
        return data

    def save_json(self, file_name, object_name):
        with open(file_name, 'w') as outfile:
            json.dump(object_name, outfile)

    async def add_vid_subs(self, vid_in,  vid_out):
        subprocess.call(['ffmpeg', '-i', vid_in, '-vf', "subtitles=crockpot/subs.srt", "-c:a", "copy",vid_out])

    async def do_inworld(self, query, user_id, user_name, channel_id):
        out = self.chat_app(query, str(user_name), str(user_id), str(channel_id))
        python_object = json.loads(out)
        return(python_object)

    async def do_tts(self, mp3_dict_list):
        await self.merge_base64_mp3s_sox(mp3_dict_list, "crockpot/merged_sox.mp3", "crockpot/subs.srt")
    
    async def avatar_waifu(self, ctx, da_text, user_id, user_name, channel_id):
        self.clean_up()
        objects_list = await self.do_inworld(da_text, user_name, user_id, channel_id)
        reply = self.concatenate_texts(objects_list)

        await self.do_tts(objects_list)
        frame_sequence = await self.audio_analysis("crockpot/merged_sox.mp3")
        await self.create_grid_video(frame_sequence)
        await self.add_vid_subs("crockpot/output_with_audio.mp4", "crockpot/spongebob.mp4")

        msg = await ctx.reply(file=discord.File(r'crockpot/spongebob.mp4'))

   
    def setup(bot):
        bot.add_cog(FGKBot(bot))
