import re
import zipfile
from pathlib import Path

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
    # Split on assistant markers to get human+response pairs, then extract human part
    # Strategy: split on [Human] markers, then for each chunk strip the assistant reply
    chunks = _HUMAN_SPLIT_RE.split(content)
    turns = []
    for chunk in chunks[1:]:  # skip content before first [Human]
        # Cut off the assistant reply that follows
        human_text = _ASSISTANT_RE.split(chunk)[0].strip()
        if len(human_text.split()) >= 20:
            turns.append(human_text)
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


async def parse_claude_export(file_path: Path) -> list[dict]:
    suffix = file_path.suffix.lower()
    segments = []

    if suffix == ".zip":
        with zipfile.ZipFile(file_path, "r") as zf:
            md_files = [n for n in zf.namelist() if n.endswith(".md")]
            if not md_files:
                raise ValueError("No .md files found in Claude ZIP export")
            for name in md_files:
                with zf.open(name) as f:
                    content = f.read().decode("utf-8", errors="replace")
                seg = _parse_markdown_file(name, content)
                if seg:
                    segments.append(seg)

    elif file_path.is_dir():
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

    else:
        raise ValueError(f"Unsupported input: {file_path}. Expected .zip, .md, or directory")

    return segments
