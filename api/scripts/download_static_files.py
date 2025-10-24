#!/usr/bin/env python3
"""Download static files for ReDoc and Stoplight Elements offline mode."""

import urllib.request
from pathlib import Path

# Define the static directory
STATIC_DIR = Path(__file__).parent.parent / "static"

# URLs for the latest stable versions
REDOC_VERSION = "2.1.3"
ELEMENTS_VERSION = "7.7.18"

FILES_TO_DOWNLOAD = {
    # ReDoc
    f"https://cdn.jsdelivr.net/npm/redoc@{REDOC_VERSION}/bundles/redoc.standalone.js": "redoc.standalone.js",
    # Stoplight Elements
    f"https://unpkg.com/@stoplight/elements@{ELEMENTS_VERSION}/web-components.min.js": "elements.min.js",
    f"https://unpkg.com/@stoplight/elements@{ELEMENTS_VERSION}/styles.min.css": "elements.min.css",
}


def download_file(url: str, destination: Path) -> None:
    """Download a file from URL to destination."""
    print(f"Downloading {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
            destination.write_bytes(content)
            print(f"  ✓ Saved to {destination}")
    except Exception as e:
        print(f"  ✗ Failed to download {url}: {e}")


def main() -> None:
    """Download all required static files."""
    # Create static directory if it doesn't exist
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Static directory: {STATIC_DIR}\n")

    # Download all files
    for url, filename in FILES_TO_DOWNLOAD.items():
        destination = STATIC_DIR / filename
        download_file(url, destination)

    print("\n✓ All files downloaded successfully!")
    print(f"\nFiles are saved in: {STATIC_DIR}")


if __name__ == "__main__":
    main()
