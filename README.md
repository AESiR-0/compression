# Video Compression Service

A FastAPI-based service for compressing MP4 videos to a target size while maintaining quality.

## Prerequisites

- Python 3.8+
- FFmpeg installed on your system
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd video-compression-service
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. The service will be available at `http://localhost:8000`

## API Endpoints

### POST /compress-mp4

Compress an MP4 video file to a target size.

**Parameters:**
- `video`: MP4 file (form-data)
- `target_size_mb`: Target size in megabytes (default: 8.0)
- `maintain_aspect_ratio`: Whether to maintain the aspect ratio (default: true)

**Response:**
- Compressed video file

### GET /health

Health check endpoint.

**Response:**
```json
{
    "status": "healthy"
}
```

## Features

- Video compression with target size
- Maintains aspect ratio (optional)
- Temporary file cleanup
- Progress tracking
- Error handling

## Notes

- The service uses FFmpeg for video compression
- Temporary files are automatically cleaned up after processing
- Only MP4 files are supported
- The compression process uses a two-pass encoding for better quality

## License

MIT 