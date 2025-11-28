from __future__ import annotations
import os
import tempfile
import asyncio
from pathlib import Path
from subprocess import CalledProcessError, run
import subprocess
import json
from io import BytesIO
import shutil


def extract_audio_to_wav(
    *,
    src_bytes: bytes | None = None,
    src_path: str | Path | None = None,
    sr: int = 16_000,
) -> str:
    """
    Convert any audio/video file (bytes or on-disk path) to a
    16-kHz mono PCM WAV.  Return the temp-file path; caller must delete it.
    """
    if bool(src_bytes) == bool(src_path):
        raise ValueError("pass either src_bytes OR src_path")

    tmp_in_name: str | None = None
    if src_bytes is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
            tmp.write(src_bytes)
            tmp_in_name = tmp.name
            src_path = tmp_in_name
    fd, out_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    os.unlink(out_path)
    try:
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "warning",
                "-i",
                str(src_path),
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                str(sr),
                "-ac",
                "1",
                out_path,
            ],
            check=True,
        )
        return out_path
    except CalledProcessError as e:
        detail = (e.stderr or b"").decode(errors="ignore")
        raise RuntimeError(f"ffmpeg failed ({e.returncode}): {detail}") from e
    finally:
        if tmp_in_name:
            try:
                os.remove(tmp_in_name)
            except OSError:
                pass


def transcode_to_webm_opus(
    src_bytes: bytes, kbps: int = 24, sr: int = 16000
) -> BytesIO:
    """
    Compress audio to mono 16kHz Opus/WebM for Whisper.
    Returns a BytesIO object ready for API upload.
    """
    with tempfile.NamedTemporaryFile(suffix=".in", delete=False) as inp:
        inp.write(src_bytes)
        inp.flush()
        in_path = inp.name
    out_path = in_path + ".webm"
    try:
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                in_path,
                "-ac",
                "1",
                "-ar",
                str(sr),
                "-c:a",
                "libopus",
                "-b:a",
                f"{kbps}k",
                "-vn",
                out_path,
            ]
        )
        with open(out_path, "rb") as f:
            buf = BytesIO(f.read())
        buf.seek(0)
        buf.name = "audio.webm"
        return buf
    finally:
        for p in (in_path, out_path):
            try:
                os.remove(p)
            except Exception:
                pass


def split_to_opus_chunks(
    src_bytes: bytes, chunk_minutes: int = 8, kbps: int = 24
) -> list[BytesIO]:
    """
    Split audio into fixed-duration Opus chunks (default 8 min).
    Returns a list of BytesIO chunks.
    """
    with tempfile.NamedTemporaryFile(suffix=".in", delete=False) as inp:
        inp.write(src_bytes)
        inp.flush()
        in_path = inp.name
    out_dir = tempfile.mkdtemp()
    pattern = os.path.join(out_dir, "part_%03d.webm")
    try:
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                in_path,
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "libopus",
                "-b:a",
                f"{kbps}k",
                "-f",
                "segment",
                "-segment_time",
                str(chunk_minutes * 60),
                "-vn",
                pattern,
            ]
        )
        parts = sorted(
            [
                os.path.join(out_dir, f)
                for f in os.listdir(out_dir)
                if f.startswith("part_")
            ]
        )
        bufs = []
        for p in parts:
            with open(p, "rb") as f:
                b = BytesIO(f.read())
            b.seek(0)
            b.name = os.path.basename(p)
            bufs.append(b)
        return bufs
    finally:
        try:
            os.remove(in_path)
        except Exception:
            pass


async def get_audio_duration(src: bytes | BytesIO, file_id: str | None = None) -> float:
    """
    Return duration (seconds) of an audio/video blob.
    Works with raw bytes or a BytesIO stream. Ignores file_id (kept for compatibility).
    Uses ffprobe if available; falls back to mutagen if needed.
    """
    # Normalize to bytes
    if isinstance(src, BytesIO):
        src.seek(0)
        data = src.read()
    elif isinstance(src, (bytes, bytearray)):
        data = bytes(src)
    else:
        raise TypeError(
            f"get_audio_duration(): expected bytes or BytesIO, got {type(src)!r}"
        )

    # Write to a temp file
    fd, tmp_path = tempfile.mkstemp(suffix=".audio")
    os.close(fd)
    try:
        loop = asyncio.get_running_loop()

        def write_temp():
            with open(tmp_path, "wb") as f:
                f.write(data)

        await loop.run_in_executor(None, write_temp)

        # Try ffprobe first
        if shutil.which("ffprobe"):
            try:
                # Ask only for the 'format=duration' field as JSON
                def run_ffprobe():
                    return subprocess.run(
                        [
                            "ffprobe",
                            "-v",
                            "error",
                            "-select_streams",
                            "a:0",
                            "-show_entries",
                            "format=duration",
                            "-of",
                            "json",
                            tmp_path,
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                proc = await loop.run_in_executor(None, run_ffprobe)
                info = json.loads(proc.stdout or "{}")
                dur = None
                # ffprobe returns duration under format.duration
                if isinstance(info, dict):
                    fmt = info.get("format") or {}
                    dur = fmt.get("duration")
                if dur is not None:
                    return float(dur)
            except Exception:
                # Fall through to mutagen
                pass

        # Fallback: mutagen (pure Python)
        try:
            from mutagen import File as MutagenFile

            mf = MutagenFile(tmp_path)
            if mf and getattr(mf, "info", None) and getattr(mf.info, "length", None):
                return float(mf.info.length)
        except Exception:
            pass

        # As a last resort, return 0.0 instead of crashing the pipeline
        return 0.0

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
