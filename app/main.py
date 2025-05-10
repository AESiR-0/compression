from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from app.ffmpeg_handler import compress_video
from app.utils import save_blob_file, cleanup_temp_files, read_file_as_bytes
import uuid
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Video Compression Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://daftaros.com"],  # Allows requests from your Next.js application
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/", response_class=HTMLResponse)
async def get_upload_form():
    return """
    <html>
        <head>
            <title>Video Compression Service</title>
        </head>
        <body>
            <h1>Upload MP4 Video for Compression</h1>
            <form action="/compress-mp4" method="post" enctype="multipart/form-data">
                <p>
                    <label for="video">Select MP4 file:</label><br>
                    <input type="file" id="video" name="video" accept="video/mp4" required>
                </p>
                <p>
                    <label for="target_size_mb">Target size (MB):</label><br>
                    <input type="number" id="target_size_mb" name="target_size_mb" value="8.0" step="0.1" min="0.1">
                </p>
                <p>
                    <label for="maintain_aspect_ratio">Maintain aspect ratio:</label>
                    <input type="checkbox" id="maintain_aspect_ratio" name="maintain_aspect_ratio" checked>
                </p>
                <input type="submit" value="Compress Video">
            </form>
        </body>
    </html>
    """
@app.post("/compress-mp4")
async def compress_video_endpoint(
    video: UploadFile = File(...),
    target_size_mb: float = Form(8.0),
    maintain_aspect_ratio: bool = Form(True)
):
    try:
        if not video.filename.lower().endswith('.mp4'):
            raise HTTPException(status_code=400, detail="Only MP4 files are supported")
        
        logger.info(f"Processing video: {video.filename}")
        logger.info(f"Target size: {target_size_mb}MB, Maintain aspect ratio: {maintain_aspect_ratio}")
        
        # Generate unique ID for this compression job
        job_id = str(uuid.uuid4())
        logger.info(f"Job ID: {job_id}")
        
        try:
            # Read the file content
            content = await video.read()
            if not content:
                raise HTTPException(status_code=400, detail="No file content provided")
            
            logger.info(f"File size before compression: {len(content) / (1024*1024):.2f}MB")
            
            # Save blob to temporary file
            input_path = await save_blob_file(content, job_id)
            logger.info(f"Saved input file to: {input_path}")
            
            # Check if ffmpeg is available
            if not os.system("ffmpeg -version") == 0:
                raise HTTPException(status_code=500, detail="FFmpeg is not installed or not available in PATH")
            
            # Compress the video
            output_path = await compress_video(
                input_path,
                target_size_mb,
                maintain_aspect_ratio
            )
            logger.info(f"Compression complete. Output file: {output_path}")
            
            # Read the compressed file as bytes
            compressed_content = await read_file_as_bytes(output_path)
            logger.info(f"File size after compression: {len(compressed_content) / (1024*1024):.2f}MB")
            
            # Return the compressed file as binary response
            return Response(
                content=compressed_content,
                media_type="video/mp4",
                headers={
                    "Content-Disposition": f'attachment; filename="compressed_{video.filename}"'
                }
            )
        
        except FileNotFoundError as e:
            logger.error(f"File not found error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"File operation failed: {str(e)}")
        except PermissionError as e:
            logger.error(f"Permission error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Permission denied: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during processing: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")
        
    finally:
        # Cleanup temporary files
        try:
            await cleanup_temp_files(job_id)
            logger.info(f"Cleaned up temporary files for job {job_id}")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 