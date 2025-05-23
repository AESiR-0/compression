import os
import subprocess
from pathlib import Path
from app.utils import get_video_output_path
import logging

logger = logging.getLogger(__name__)

def get_video_info(input_path: str) -> dict:
    """Get video information using ffprobe"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate",
        "-show_entries", "format=duration,bit_rate",
        "-of", "json",
        input_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe error: {e.stderr}")
        raise RuntimeError(f"Failed to get video information: {e.stderr}")

def get_video_duration(input_path: str) -> float:
    """Get video duration in seconds using ffprobe"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe error: {e.stderr}")
        raise RuntimeError(f"Failed to get video duration: {e.stderr}")

def get_video_bitrate(input_path: str) -> int:
    """Get video bitrate in bits per second using ffprobe"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return int(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe error: {e.stderr}")
        raise RuntimeError(f"Failed to get video bitrate: {e.stderr}")

async def compress_video(
    input_path: str,
    target_size_mb: float,
    maintain_aspect_ratio: bool
) -> str:
    """Compress video to target size using FFmpeg"""
    # Get video information
    video_info = get_video_info(input_path)
    logger.info(f"Video information: {video_info}")
    
    # Calculate target bitrate
    duration = get_video_duration(input_path)
    target_size_bits = target_size_mb * 8 * 1024 * 1024
    target_bitrate = int(target_size_bits / duration)
    
    job_id = str(Path(input_path).parent.name)
    output_path = get_video_output_path(input_path, job_id)
    
    # Build FFmpeg command with improved codec selection
    base_cmd = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx264",  # Use H.264 codec
        "-preset", "medium",  # Balance between speed and quality
        "-crf", "23",  # Constant Rate Factor for quality
        "-b:v", f"{target_bitrate}",
        "-maxrate", f"{target_bitrate * 1.5}",  # Maximum bitrate
        "-bufsize", f"{target_bitrate * 2}",  # Buffer size
        "-pass", "1",
        "-f", "mp4"
    ]
    
    if maintain_aspect_ratio:
        base_cmd.extend(["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"])
    
    # First pass
    first_pass = base_cmd + ["-y", "NUL"]
    try:
        logger.info("Starting first pass encoding")
        subprocess.run(first_pass, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"First pass encoding failed: {e.stderr}")
        raise RuntimeError(f"First pass encoding failed: {e.stderr}")
    
    # Second pass with improved audio handling
    second_pass = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-b:v", f"{target_bitrate}",
        "-maxrate", f"{target_bitrate * 1.5}",
        "-bufsize", f"{target_bitrate * 2}",
        "-pass", "2",
        "-c:a", "aac",  # Use AAC for audio
        "-b:a", "128k",  # Audio bitrate
        "-ar", "44100",  # Audio sample rate
        "-ac", "2"  # Stereo audio
    ]
    
    if maintain_aspect_ratio:
        second_pass.extend(["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"])
    
    second_pass.extend(["-y", output_path])
    
    try:
        logger.info("Starting second pass encoding")
        subprocess.run(second_pass, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Second pass encoding failed: {e.stderr}")
        raise RuntimeError(f"Second pass encoding failed: {e.stderr}")
    
    return output_path 