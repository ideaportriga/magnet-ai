import sys
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    # Add the 'src' directory to the Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    # Run the uvicorn server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
