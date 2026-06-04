import re
from dataclasses import dataclass

from app.cell_utils import normalize_cell

THREE_DIGIT_PATTERN = re.compile(r"^\d{3}$")
ROOM_TOKEN_PATTERN = re.compile(r"\b(\d{3})\b")


@dataclass
class ResponsibleEntry:
    name: str
    rooms: list[str]


def normalize_room(value: str) -> str:
    text = normalize_cell(value).strip()
    if not text:
        return ""
    if THREE_DIGIT_PATTERN.match(text):
        return text
    match = ROOM_TOKEN_PATTERN.search(text)
    return match.group(1) if match else ""


def parse_rooms_text(value: str) -> list[str]:
    text = normalize_cell(value)
    if not text:
        return []
    parts = re.split(r"[,;\s]+", text)
    rooms: list[str] = []
    seen: set[str] = set()
    for part in parts:
        room = normalize_room(part)
        if room and room not in seen:
            seen.add(room)
            rooms.append(room)
    return rooms


def build_room_index(entries: list[ResponsibleEntry]) -> dict[str, str]:
    index: dict[str, str] = {}
    for entry in entries:
        name = entry.name.strip()
        if not name:
            continue
        for room in entry.rooms:
            if room not in index:
                index[room] = name
    return index


def resolve_responsible_lines(rooms: list[str], room_index: dict[str, str]) -> list[str]:
    return [room_index.get(normalize_room(room), "") for room in rooms]


def _responsible_key(value: str) -> str:
    return normalize_cell(value).strip().casefold()


def responsible_merge_spans_for_group(
    responsibles: list[str],
) -> list[tuple[int, int]]:
    """Индексы [start, end) внутри группы для объединения одинаковых ответственных."""
    return responsible_merge_spans(responsibles, 0, len(responsibles))


def responsible_merge_spans(
    responsibles: list[str],
    block_start: int,
    block_end: int,
) -> list[tuple[int, int]]:
    """Индексы [start, end) в диапазоне строк для объединения ячеек ответственного."""
    spans: list[tuple[int, int]] = []
    index = block_start

    while index < block_end:
        anchor = _responsible_key(responsibles[index])
        if not anchor:
            index += 1
            continue

        end = index + 1
        while end < block_end:
            current = _responsible_key(responsibles[end])
            if current and current != anchor:
                break
            end += 1

        if end - index > 1:
            spans.append((index - block_start, end - block_start))
        index = end

    return spans


def _schedule_blocks(times: list[str]) -> list[tuple[int, int]]:
    if not times:
        return []
    blocks: list[tuple[int, int]] = []
    start = 0
    for index in range(1, len(times)):
        if times[index].strip():
            blocks.append((start, index))
            start = index
    blocks.append((start, len(times)))
    return blocks


def _roster_key(values: list[str]) -> tuple[str, ...]:
    roster: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        roster.append(key)
    return tuple(roster)


def format_responsible_lines(times: list[str], responsible: list[str]) -> list[str]:
    """Show specialist on the row of their room; skip block if roster unchanged."""
    if not responsible:
        return []

    result = [""] * len(responsible)
    prev_roster: tuple[str, ...] | None = None

    for start, end in _schedule_blocks(times):
        block_values = [responsible[index] for index in range(start, end)]
        roster = _roster_key(block_values)
        if not roster:
            continue
        if roster == prev_roster:
            continue

        seen_in_block: set[str] = set()
        for index in range(start, end):
            name = responsible[index].strip()
            if not name:
                continue
            key = name.casefold()
            if key in seen_in_block:
                continue
            result[index] = name
            seen_in_block.add(key)

        prev_roster = roster

    return result
