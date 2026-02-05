import json
import re
from typing import Any


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) < 2:
        return stripped

    start = 1
    end = len(lines)
    while end > start and not lines[end - 1].strip().startswith("```"):
        end -= 1
    if end <= start:
        return stripped

    return "\n".join(lines[start : end - 1]).strip()


def _try_parse_json_object(text: str) -> dict[str, Any] | None:
    candidate = _strip_code_fences(text)
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    # Fallback: try to find a JSON object substring (common when the model adds prose).
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start < 0 or end <= start:
        return None

    try:
        parsed = json.loads(candidate[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _normalize_speaker_label(label: str) -> str | None:
    """
    Normalize diarization speaker labels to a stable form used in transcripts.

    Examples:
      - "speaker_0" -> "speaker_0"
      - "SPEAKER_00" -> "speaker_0"
    """

    match = re.match(r"(?i)^speaker_(\d+)$", str(label or "").strip())
    if not match:
        return None
    try:
        return f"speaker_{int(match.group(1))}"
    except Exception:
        return None


def _coerce_speaker_mapping(value: Any) -> dict[str, str]:
    if not value:
        return {}

    mapping: dict[str, str] = {}
    if isinstance(value, dict):
        for key, name in value.items():
            if key is None:
                continue
            speaker_key = str(key).strip()
            speaker_norm = _normalize_speaker_label(speaker_key) or speaker_key
            speaker_name = str(name or "").strip()
            if speaker_name:
                mapping[speaker_norm] = speaker_name
        return mapping

    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            speaker = item.get("speaker") or item.get("id") or item.get("label")
            name = item.get("name") or item.get("display_name") or item.get("full_name")
            if not speaker or not name:
                continue
            speaker_key = str(speaker).strip()
            speaker_norm = _normalize_speaker_label(speaker_key) or speaker_key
            speaker_name = str(name).strip()
            if speaker_name:
                mapping[speaker_norm] = speaker_name
        return mapping

    return {}


def annotate_transcript_speakers(
    transcript: str, speaker_mapping: dict[str, str]
) -> str:
    if not transcript or not speaker_mapping:
        return transcript

    normalized_mapping: dict[str, str] = {}
    for key, value in speaker_mapping.items():
        norm = _normalize_speaker_label(key) or str(key).strip()
        name = str(value or "").strip()
        if norm and name:
            normalized_mapping[norm] = name

    if not normalized_mapping:
        return transcript

    pattern = re.compile(
        r"(?P<label>\b(?:speaker|SPEAKER)_(?:0*\d+)\b)(?!\s*\()(?=\s*:)"
    )

    def _replace(match: re.Match[str]) -> str:
        label = match.group("label")
        norm = _normalize_speaker_label(label) or label
        name = normalized_mapping.get(norm) or normalized_mapping.get(label)
        if not name:
            return label
        return f"{label} ({name})"

    return pattern.sub(_replace, transcript)


def parse_speaker_mapping_output(text: str) -> dict[str, str]:
    """
    Parse a post-transcription template output that is expected to return ONLY a
    speaker mapping JSON, e.g.:

      {"speaker_mapping": {"speaker_0": "Oleg", "speaker_1": "Anna"}}
    """

    obj = _try_parse_json_object(text)
    if not obj:
        return {}

    mapping_value = None
    for key in (
        "speaker_mapping",
        "speaker_map",
        "speaker_names",
        "speakers",
        "mapping",
    ):
        if key in obj:
            mapping_value = obj.get(key)
            break

    mapping = _coerce_speaker_mapping(mapping_value)
    if mapping:
        return mapping

    # Optional: accept a plain mapping object as the root.
    root_mapping = _coerce_speaker_mapping(obj)
    if root_mapping:
        return root_mapping

    return {}
