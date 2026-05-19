import json
import re
import zipfile
from pathlib import Path

from core.processing.anonymize import anonymize, check_zip_size

# Match [Human] turns — handles both \n\n[Human]\n and \n\nHuman: formats
_HUMAN_SPLIT_RE = re.compile(
    r'\n{1,2}(?:\[Human\]|Human:)\s*',
    re.IGNORECASE,
)
_ASSISTANT_RE = re.compile(
    r'\n{1,2}(?:\[Assistant\]|Assistant:)\s*',
    re.IGNORECASE,
)


def _extract_human_turns(content: str) -> list[str]:
    chunks = _HUMAN_SPLIT_RE.split(content)
    turns = []
    for chunk in chunks[1:]:
        human_text = _ASSISTANT_RE.split(chunk)[0].strip()
        if len(human_text.split()) >= 20:
            turns.append(anonymize(human_text))
    return turns


def _parse_markdown_file(name: str, content: str) -> dict | None:
    turns = _extract_human_turns(content)
    if not turns:
        return None
    stem = Path(name).stem
    return {
        "conversation_id": stem,
        "messages": turns,
        "source": "claude",
        "created_at": None,
    }


def _parse_conversations_json(data: list) -> list[dict]:
    segments = []
    for conv in data:
        if not isinstance(conv, dict):
            continue
        messages = conv.get("chat_messages", [])
        human_turns = []
        for msg in messages:
            if msg.get("sender") != "human":
                continue
            # Prefer top-level text, fall back to content[].text
            text = msg.get("text", "").strip()
            if not text:
                for block in msg.get("content", []):
                    text = block.get("text", "").strip()
                    if text:
                        break
            if text and len(text.split()) >= 20:
                human_turns.append(anonymize(text))
        if human_turns:
            segments.append({
                "conversation_id": conv.get("uuid", ""),
                "messages": human_turns,
                "source": "claude",
                "created_at": conv.get("created_at"),
            })
    return segments


async def parse_claude_export(file_path: Path) -> list[dict]:
    suffix = file_path.suffix.lower()
    segments = []

    if suffix == ".zip":
        with zipfile.ZipFile(file_path, "r") as zf:
            check_zip_size(zf)
            names = zf.namelist()
            # Prefer JSON export format (conversations.json)
            if "conversations.json" in names:
                with zf.open("conversations.json") as f:
                    data = json.loads(f.read().decode("utf-8", errors="replace"))
                segments = _parse_conversations_json(data)
            else:
                md_files = [n for n in names if n.endswith(".md")]
                if not md_files:
                    raise ValueError("No conversations.json or .md files found in Claude ZIP export")
                for name in md_files:
                    with zf.open(name) as f:
                        content = f.read().decode("utf-8", errors="replace")
                    seg = _parse_markdown_file(name, content)
                    if seg:
                        segments.append(seg)

    elif file_path.is_dir():
        json_file = file_path / "conversations.json"
        if json_file.exists():
            data = json.loads(json_file.read_text(encoding="utf-8"))
            segments = _parse_conversations_json(data)
        else:
            for md_file in file_path.glob("*.md"):
                content = md_file.read_text(encoding="utf-8", errors="replace")
                seg = _parse_markdown_file(md_file.name, content)
                if seg:
                    segments.append(seg)

    elif suffix == ".md":
        content = file_path.read_text(encoding="utf-8", errors="replace")
        seg = _parse_markdown_file(file_path.name, content)
        if seg:
            segments.append(seg)

    elif suffix == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        segments = _parse_conversations_json(data)

    else:
        raise ValueError(f"Unsupported input: {file_path}. Expected .zip, .json, .md, or directory")

    return segments
