"""Media handling utilities for Neku Bot."""

import base64
import json
import os
import subprocess
import tempfile
from datetime import timedelta

import cv2
import librosa
import numpy as np


# Grid loading ---------------------------------------------------------------

def load_grid(rows: int = 3, folder: str = "vids"):
    """Load video frames into a grid structure."""
    grid = [[] for _ in range(rows)]
    for i in range(rows):
        video_path = f"{folder}/{i}.mp4"
        if not os.path.isfile(video_path):
            print(f"Warning: {video_path} not found. Skipping.")
            continue
        video = cv2.VideoCapture(video_path)
        while video.isOpened():
            ret, frame = video.read()
            if not ret:
                break
            grid[i].append(frame)
        video.release()
    print("Frames loaded")
    return grid


# Audio helpers --------------------------------------------------------------

async def audio_analysis(filepath: str):
    """Analyse an audio file and classify its volume over time."""
    fps = 16
    frame_length = 1 / fps
    y, sr = librosa.load(filepath)
    frame_samples = int(sr * frame_length)
    frames = [y[i : i + frame_samples] for i in range(0, len(y), frame_samples)]
    volume_class = []
    for frame in frames:
        rms = np.sqrt(np.mean(frame ** 2))
        volume_class.append(0 if rms < 0.1 else 1 if rms < 0.125 else 2)
    return volume_class


def concatenate_texts(objects_list):
    """Concatenate the ``text`` field of objects in a list."""
    return "".join(obj["text"] for obj in objects_list)


async def merge_base64_mp3s_sox(mp3_dict_list, output_file, srt_file_path):
    """Merge multiple base64 MP3 blobs into a single file using SoX."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mp3_file_paths = []
        srt_entries = []
        current_time = timedelta()
        for i, mp3_dict in enumerate(mp3_dict_list):
            mp3_data = base64.b64decode(mp3_dict["audio"])
            mp3_file_path = os.path.join(tmp_dir, f"segment_{i}.mp3")
            with open(mp3_file_path, "wb") as f:
                f.write(mp3_data)
            mp3_file_paths.append(mp3_file_path)
            duration = get_duration_ffprobe(mp3_file_path)
            end_time = current_time + timedelta(seconds=duration)
            srt_entries.append((i + 1, current_time, end_time, mp3_dict["text"]))
            current_time = end_time
        sox_cmd = ["sox", *mp3_file_paths, output_file]
        subprocess.run(sox_cmd, check=True)
        write_srt_file(srt_entries, srt_file_path)


def get_duration_ffprobe(mp3_file_path: str) -> float:
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
    return float(ffprobe_data["format"]["duration"])


def format_timedelta(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def write_srt_file(srt_entries, srt_file_path: str) -> None:
    with open(srt_file_path, "w", encoding="utf-8") as f:
        for entry in srt_entries:
            f.write(f"{entry[0]}\n")
            f.write(f"{format_timedelta(entry[1])} --> {format_timedelta(entry[2])}\n")
            f.write(f"{entry[3]}\n\n")


async def create_grid_video(frame_sequence, grid, output_file: str = "crockpot/output_video.mp4"):
    """Generate a grid video from the provided frame sequence."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    output_video = cv2.VideoWriter(output_file, fourcc, 16.0, (512, 512))
    for i, A in enumerate(frame_sequence):
        frame = grid[A][i % 32]
        output_video.write(frame)
    output_video.release()
    cv2.destroyAllWindows()
    command = [
        "ffmpeg",
        "-i",
        output_file,
        "-i",
        "crockpot/merged_sox.mp3",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-shortest",
        "crockpot/output_with_audio.mp4",
    ]
    subprocess.run(command)


async def add_vid_subs(vid_in: str, vid_out: str):
    subprocess.call([
        "ffmpeg",
        "-i",
        vid_in,
        "-vf",
        "subtitles=crockpot/subs.srt",
        "-c:a",
        "copy",
        vid_out,
    ])


def clean_up() -> None:
    os.system("rm crockpot/*")


async def do_tts(mp3_dict_list):
    await merge_base64_mp3s_sox(mp3_dict_list, "crockpot/merged_sox.mp3", "crockpot/subs.srt")
