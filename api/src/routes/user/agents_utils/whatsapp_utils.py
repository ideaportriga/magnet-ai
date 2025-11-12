import hashlib
import hmac
from typing import Any


def extract_whatsapp_phone_number_id(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None

    entries = payload.get("entry")
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue

            changes = entry.get("changes")
            if isinstance(changes, list):
                for change in changes:
                    if not isinstance(change, dict):
                        continue

                    value = change.get("value")
                    if isinstance(value, dict):
                        metadata = value.get("metadata")
                        if isinstance(metadata, dict):
                            phone_number_id = metadata.get("phone_number_id")
                            if isinstance(phone_number_id, str) and phone_number_id:
                                return phone_number_id

                        phone_number_id = value.get("phone_number_id")
                        if isinstance(phone_number_id, str) and phone_number_id:
                            return phone_number_id

            entry_id = entry.get("id")
            if isinstance(entry_id, str) and entry_id:
                return entry_id

    return None


def verify_whatsapp_signature(
    signature: str, raw_body: bytes, app_secret: str | None
) -> bool:
    if not app_secret:
        return False

    if not signature:
        return False

    algo_name = "sha256"
    provided = signature
    if "=" in signature:
        prefix, candidate = signature.split("=", 1)
        if not candidate:
            return False
        provided = candidate
        if prefix and prefix.lower() != algo_name:
            return False

    digest = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided, digest)
