import os
import sys
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    # Add the 'src' directory to the Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    # Get port from environment variable, default to 8000
    port = int(os.getenv("PORT", 8000))

    # Run the uvicorn server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
