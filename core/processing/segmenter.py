import re
from datetime import datetime, timezone

from llm.embeddings import cosine_similarity, embed

_TOPIC_CHANGE_RE = re.compile(
    r'^(different question|anyway[,.]|moving on|on a separate|changing topic|by the way|'
    r'btw[,.]|new question|unrelated|forget that|switching to)',
    re.IGNORECASE,
)

MIN_WORDS = 30
EMBED_SPLIT_THRESHOLD = 0.70  # cosine distance above this → new segment (conservative)
MIN_MESSAGES_FOR_EMBED_SPLIT = 5  # only use embedding split on larger groups
TIME_GAP_HOURS = 24


def _parse_ts(ts_str: str | None) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return None


def _word_count(messages: list[str]) -> int:
    return sum(len(m.split()) for m in messages)


def _split_by_topic(messages: list[str]) -> list[list[str]]:
    """Split a message list into sub-groups using embedding distance."""
    if len(messages) < 3:
        return [messages]

    groups: list[list[str]] = [[messages[0]]]
    for msg in messages[1:]:
        prev_text = groups[-1][-1]
        try:
            sim = cosine_similarity(embed(prev_text[-200:]), embed(msg[:200]))
            distance = 1.0 - sim
        except Exception:
            distance = 0.0

        if distance > EMBED_SPLIT_THRESHOLD:
            groups.append([msg])
        else:
            groups[-1].append(msg)

    return groups


async def segment(raw_segments: list[dict]) -> list[dict]:
    result: list[dict] = []
    seg_index = 0

    for raw in raw_segments:
        messages: list[str] = raw.get("messages", [])
        created_at = raw.get("created_at")
        source = raw.get("source", "unknown")
        conv_id = raw.get("conversation_id", "unknown")

        if not messages:
            continue

        # Step 1 — split on explicit topic change phrases
        phrase_groups: list[list[str]] = [[]]
        for msg in messages:
            if _TOPIC_CHANGE_RE.match(msg) and phrase_groups[-1]:
                phrase_groups.append([msg])
            else:
                phrase_groups[-1].append(msg)

        # Step 2 — split on embedding distance (only for larger groups)
        embed_groups: list[list[str]] = []
        for group in phrase_groups:
            if len(group) >= MIN_MESSAGES_FOR_EMBED_SPLIT:
                sub = _split_by_topic(group)
                # Only keep the split if all resulting sub-groups meet minimum word count
                if all(_word_count(s) >= MIN_WORDS for s in sub):
                    embed_groups.extend(sub)
                else:
                    embed_groups.append(group)
            else:
                embed_groups.append(group)

        # Step 3 — emit segments that meet minimum word count
        for group in embed_groups:
            if _word_count(group) < MIN_WORDS:
                continue
            result.append({
                "conversation_id": conv_id,
                "messages": group,
                "source": source,
                "created_at": created_at,
                "segment_index": seg_index,
                "classification": None,
            })
            seg_index += 1

    return result
