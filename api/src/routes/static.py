"""Static files route handlers."""

from pathlib import Path
from litestar import get
from litestar.response import File
from litestar.exceptions import NotFoundException


STATIC_DIR = Path(__file__).parent.parent.parent / "static"

# MIME types mapping
MIME_TYPES = {
    ".css": "text/css",
    ".js": "application/javascript",
    ".map": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}


@get("/static/{file_name:str}", include_in_schema=False)
async def serve_static_file(file_name: str) -> File:
    """Serve static files for Swagger UI and ReDoc."""
    file_path = STATIC_DIR / file_name
    
    if not file_path.exists():
        raise NotFoundException(f"Static file not found: {file_name}")
    
    # Determine media type from file extension
    file_ext = file_path.suffix.lower()
    media_type = MIME_TYPES.get(file_ext, "text/plain")
    
    return File(path=file_path, media_type=media_type)
