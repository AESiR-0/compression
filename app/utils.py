import os
import shutil
from pathlib import Path
import aiofiles

TEMP_DIR = Path(__file__).parent / "temp"

async def save_blob_file(content: bytes, job_id: str) -> str:
    """Save binary content to temporary directory"""
    # Create job directory
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = job_dir / f"input.mp4"
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(content)
    
    return str(file_path)

async def read_file_as_bytes(file_path: str) -> bytes:
    """Read file content as bytes"""
    async with aiofiles.open(file_path, "rb") as file:
        return await file.read()

async def cleanup_temp_files(job_id: str):
    """Remove temporary files after processing"""
    job_dir = TEMP_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)

def get_video_output_path(input_path: str, job_id: str) -> str:
    """Generate output path for compressed video"""
    job_dir = TEMP_DIR / job_id
    return str(job_dir / "output.mp4") 