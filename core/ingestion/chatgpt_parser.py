import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from core.processing.anonymize import anonymize, check_zip_size

# Cap on conversations we process per export. Multi-year exports can contain
# 5–10k conversations; running each through embed + classify + extract would
# burn through the Groq 14.4k req/day free tier and take hours. The cap is on
# most-recent-first slice (sorted by create_time desc).
MAX_CONVERSATIONS_PER_EXPORT = 1000


def _timestamp_to_iso(ts) -> str | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except Exception:
        return None


def _extract_messages_from_mapping(mapping: dict) -> list[str]:
    """Extract user messages from ChatGPT's tree-structured mapping format."""
    messages = []
    for node in mapping.values():
        msg = node.get("message")
        if not msg:
            continue
        if msg.get("author", {}).get("role") != "user":
            continue
        content = msg.get("content", {})
        parts = content.get("parts", [])
        text = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
        if len(text.split()) >= 20:
            messages.append(anonymize(text))
    return messages


def _extract_messages_legacy(messages_list: list) -> list[str]:
    """Handle older ChatGPT export format with flat messages list."""
    results = []
    for msg in messages_list:
        if msg.get("role") != "user":
            continue
        text = msg.get("content", "").strip()
        if len(text.split()) >= 20:
            results.append(anonymize(text))
    return results


def _parse_conversations(data: list) -> list[dict]:
    segments = []
    for conv in data:
        conv_id = conv.get("id", "unknown")
        created_at = _timestamp_to_iso(conv.get("create_time"))

        if "mapping" in conv:
            messages = _extract_messages_from_mapping(conv["mapping"])
        elif "messages" in conv:
            messages = _extract_messages_legacy(conv["messages"])
        else:
            continue

        if messages:
            segments.append({
                "conversation_id": conv_id,
                "messages": messages,
                "source": "chatgpt",
                "created_at": created_at,
            })
    return segments


async def parse_chatgpt_export(file_path: Path) -> list[dict]:
    suffix = file_path.suffix.lower()

    if suffix == ".zip":
        with zipfile.ZipFile(file_path, "r") as zf:
            check_zip_size(zf)
            names = zf.namelist()
            json_file = next(
                (n for n in names if n.endswith("conversations.json")), None
            )
            if not json_file:
                raise ValueError("conversations.json not found in ChatGPT ZIP export")
            with zf.open(json_file) as f:
                data = json.load(f)
    elif suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Expected .zip or .json")

    if not isinstance(data, list):
        raise ValueError("conversations.json must be a JSON array of conversations")

    # Cap to the most recent N conversations (by create_time) so the extraction
    # pipeline doesn't run for hours / blow the API rate limit on multi-year exports.
    if len(data) > MAX_CONVERSATIONS_PER_EXPORT:
        data = sorted(data, key=lambda c: c.get("create_time") or 0, reverse=True)
        data = data[:MAX_CONVERSATIONS_PER_EXPORT]

    return _parse_conversations(data)
