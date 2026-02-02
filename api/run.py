import os
import sys
from pathlib import Path

import uvicorn


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    truthy = {"1", "true", "t", "yes", "y", "on"}
    falsy = {"0", "false", "f", "no", "n", "off"}

    if normalized in truthy:
        return True
    if normalized in falsy:
        return False

    raise ValueError(
        f"Invalid value for {name}: {value!r}. Expected one of: "
        f"{', '.join(sorted(truthy | falsy))}"
    )


if __name__ == "__main__":
    # Add the 'src' directory to the Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    # Get port from environment variable, default to 8000
    port = int(os.getenv("PORT", 8000))

    # Default behaviour is to run with auto-reload disabled.
    # You can override with UVICORN_RELOAD=true
    reload = _env_bool("UVICORN_RELOAD", False)

    # Run the uvicorn server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
    )
