import re
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

from app.cell_utils import normalize_cell
from app.modules.duty_formation.models import (
    PROGRAM_ALT_COL,
    PROGRAM_MID_COL,
    PROGRAM_NUMBER_COL,
    ROOM_COL,
    STUDENTS_COL,
    TEACHER_COL,
    GroupAggregate,
    ScheduleLine,
    SelectedRange,
)
from app.modules.duty_formation.services.responsible_mapping import (
    ResponsibleEntry,
    build_room_index,
    format_responsible_lines,
    resolve_responsible_lines,
)

TIME_RANGE_PATTERN = re.compile(
    r"\d{1,2}[.:]\d{2}\s*[–\-—−]\s*\d{1,2}[.:]\d{2}",
    re.IGNORECASE,
)
TIME_SINGLE_PATTERN = re.compile(r"^\d{1,2}[.:]\d{2}$")
TIME_START_PATTERN = re.compile(r"(\d{1,2})[.:](\d{2})")
PERSON_PATTERN = re.compile(r"[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.?")
GROUP_FULL_PATTERN = re.compile(
    r"(?:ПК|БГМУ|КО|ПП)\s*[:\s]?\s*\d+|[А-ЯЁа-яё].{4,}",
    re.IGNORECASE,
)
GROUP_PREFIX_PATTERN = re.compile(r"^(?:БГМУ|КО|ПК|ПП|И)$", re.IGNORECASE)
THREE_DIGIT_PATTERN = re.compile(r"^\d{3}$")
ID_NUMBER_PATTERN = re.compile(r"^\d{3,5}$")

SPURIOUS_TIMES = frozenset({"0:00", "00:00", "0:00:00", "00:00:00", "0.0", "0", "00.00", "0.00"})

COLUMN_ALIASES = {
    "group": ("группа", "group", "образовательн", "программ"),
    "time": ("время", "time", "занят"),
    "teacher": ("преподав", "teacher", "таб"),
    "responsible": ("ответств", "специалист", "responsible"),
    "room": ("кабинет", "симуляц", "room", "каб"),
    "prefix": ("тип", "вид", "форма", "пк", "бгму"),
}


@dataclass
class ColumnMapping:
    group: int | None = None
    group_students: int | None = None
    group_program: int | None = None
    group_program_mid: int | None = None
    group_program_alt: int | None = None
    group_prefix: int | None = None
    group_number: int | None = None
    time: int | None = None
    teacher: int | None = None
    responsible: int | None = None
    room: int | None = None
    skip: set[int] = field(default_factory=set)


def _normalize(value) -> str:
    return normalize_cell(value)


def _pad_rows(rows: list[list[str]]) -> list[list[str]]:
    if not rows:
        return []
    width = max(len(row) for row in rows)
    return [row + [""] * (width - len(row)) for row in rows]


def _is_meaningful_row(row: list[str], mapping: "ColumnMapping") -> bool:
    payload = (
        _extract_times(_cell(row, mapping.time))
        + _split_values(_cell(row, mapping.teacher))
        + _split_values(_cell(row, mapping.responsible))
        + _extract_rooms(_cell(row, mapping.room))
    )
    if payload:
        return True

    return _explicit_group_key(row, mapping) is not None


def _split_values(value: str) -> list[str]:
    text = _normalize(value)
    if not text:
        return []
    parts = re.split(r"[,;/]\s*|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def _unique_preserve(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _time_sort_key(value: str) -> tuple[int, int]:
    match = TIME_START_PATTERN.search(_normalize(value))
    if not match:
        return (99, 99)
    return int(match.group(1)), int(match.group(2))


def _earliest_time_key(times: list[str]) -> tuple[int, int]:
    if not times:
        return (99, 99)
    return min(_time_sort_key(value) for value in times)


def _is_spurious_time(value: str) -> bool:
    text = _normalize(value)
    return text in SPURIOUS_TIMES or text.startswith("1899-") or text.startswith("1900-01-01")


def _extract_times(value: str) -> list[str]:
    text = _normalize(value)
    if not text or _is_spurious_time(text):
        return []
    matches = [match.group(0).strip() for match in TIME_RANGE_PATTERN.finditer(text)]
    if matches:
        return _unique_preserve(matches)
    if TIME_SINGLE_PATTERN.match(text) and not _is_spurious_time(text):
        return [text.replace(":", ".")]
    return []


def _extract_rooms(value: str) -> list[str]:
    text = _normalize(value)
    if not text:
        return []
    parts = _split_values(text)
    rooms = [part for part in parts if THREE_DIGIT_PATTERN.match(part)]
    if rooms:
        return _unique_preserve(rooms)
    matches = [match.group(0).strip() for match in re.finditer(r"\b\d{3}\b", text)]
    return _unique_preserve(matches)


def _pad_list(items: list[str], size: int) -> list[str]:
    if size <= 0:
        return []
    if len(items) >= size:
        return items[:size]
    return items + [""] * (size - len(items))


def _times_on_line(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped:
        return [""]
    if _is_spurious_time(stripped):
        return [""]
    matches = [match.group(0).strip() for match in TIME_RANGE_PATTERN.finditer(stripped)]
    if matches:
        return matches
    if TIME_SINGLE_PATTERN.match(stripped):
        return [stripped.replace(":", ".")]
    return [""]


def _time_lines(value: str) -> list[str]:
    text = _normalize(value)
    if not text or _is_spurious_time(text):
        return []
    if "\n" in text:
        lines: list[str] = []
        for line in text.split("\n"):
            lines.extend(_times_on_line(line))
        return lines
    return _times_on_line(text)


def _text_lines(value: str) -> list[str]:
    text = _normalize(value)
    if not text:
        return []
    if "\n" in text:
        return [line.strip() for line in text.split("\n")]
    parts = _split_values(text)
    return parts if len(parts) > 1 else [text]


def _room_lines(value: str) -> list[str]:
    text = _normalize(value)
    if not text:
        return []
    if "\n" in text:
        lines: list[str] = []
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                lines.append("")
                continue
            rooms = [
                part
                for part in _split_values(stripped)
                if THREE_DIGIT_PATTERN.match(part)
            ]
            if not rooms:
                rooms = [match.group(0).strip() for match in re.finditer(r"\b\d{3}\b", stripped)]
            if len(rooms) > 1:
                lines.extend(rooms)
            elif len(rooms) == 1:
                lines.append(rooms[0])
            else:
                lines.append(stripped)
        return lines
    rooms = _extract_rooms(text)
    return rooms if rooms else [text]


def _aligned_schedule_from_row(
    row: list[str], mapping: ColumnMapping
) -> tuple[list[str], list[str], list[str], list[str]]:
    times = _time_lines(_cell(row, mapping.time))
    teachers = _text_lines(_cell(row, mapping.teacher))
    responsible = _text_lines(_cell(row, mapping.responsible))
    rooms = _room_lines(_cell(row, mapping.room))

    height = max(len(times), len(teachers), len(responsible), len(rooms))
    if height == 0:
        return [], [], [], []

    return (
        _pad_list(times, height),
        _pad_list(teachers, height),
        _pad_list(responsible, height),
        _pad_list(rooms, height),
    )


def _dedupe_key(value: str) -> str:
    return re.sub(r"\s+", "", value.casefold().replace(":", "."))


def _dedupe_preserve_lines(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = _dedupe_key(value)
        if not key:
            result.append(value)
            continue
        if key in seen:
            result.append("")
        else:
            seen.add(key)
            result.append(value)
    return result


def _roster_key(values: list[str]) -> tuple[str, ...]:
    roster: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = _dedupe_key(value)
        if not key or key in seen:
            continue
        seen.add(key)
        roster.append(key)
    return tuple(roster)


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


def _roster_display_names(values: list[str]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = _dedupe_key(value)
        if not key or key in seen:
            continue
        seen.add(key)
        names.append(value.strip())
    return names


def _schedule_line_has_content(
    time: str,
    teacher: str,
    responsible: str,
    room: str,
) -> bool:
    return any(_normalize(part) for part in (time, teacher, responsible, room))


def _compact_schedule_rows(
    times: list[str],
    teachers: list[str],
    rooms: list[str],
    teachers_source: list[str],
    responsible: list[str] | None = None,
) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    """Убирает строки без времени, преподавателя, ответственного и кабинета."""
    responsible = responsible if responsible is not None else [""] * len(times)
    times, teachers, responsible, rooms = _align_schedule_lists(
        times, teachers, responsible, rooms
    )
    source = teachers_source
    if len(source) < len(times):
        source = source + [""] * (len(times) - len(source))
    elif len(source) > len(times):
        source = source[: len(times)]

    compact_times: list[str] = []
    compact_teachers: list[str] = []
    compact_responsible: list[str] = []
    compact_rooms: list[str] = []
    compact_source: list[str] = []

    for index in range(len(times)):
        if not _schedule_line_has_content(
            times[index],
            teachers[index],
            responsible[index],
            rooms[index],
        ):
            continue
        compact_times.append(times[index])
        compact_teachers.append(teachers[index])
        compact_responsible.append(responsible[index])
        compact_rooms.append(rooms[index])
        compact_source.append(source[index])

    return (
        compact_times,
        compact_teachers,
        compact_responsible,
        compact_rooms,
        compact_source,
    )


def _append_schedule_to_bucket(
    bucket: dict[str, list[str]],
    times: list[str],
    teachers: list[str],
    rooms: list[str],
) -> None:
    """Добавляет в группу только строки с данными (без padding-пустышек)."""
    times, teachers, _, rooms = _align_schedule_lists(times, teachers, [], rooms)
    for index in range(len(times)):
        if not _schedule_line_has_content(
            times[index],
            teachers[index],
            "",
            rooms[index],
        ):
            continue
        bucket["times"].append(times[index])
        bucket["teachers"].append(teachers[index])
        bucket["rooms"].append(rooms[index])


def _time_block_border_after_indices(
    times: list[str],
    teachers_source: list[str],
) -> set[int]:
    """Индексы строк, после которых нужна граница (сменился состав преподавателей)."""
    blocks = _schedule_blocks(times)
    if len(blocks) <= 1:
        return set()

    borders: set[int] = set()
    effective_roster: tuple[str, ...] | None = None

    for block_index, (start, end) in enumerate(blocks):
        block_roster = _roster_key(teachers_source[start:end])
        if (
            block_index > 0
            and block_roster
            and effective_roster is not None
            and block_roster != effective_roster
            and start > 0
        ):
            borders.add(start - 1)

        if block_roster:
            effective_roster = block_roster

    return borders


def _build_schedule_lines(
    times: list[str],
    teachers: list[str],
    responsible: list[str],
    rooms: list[str],
    teachers_source: list[str],
) -> list[ScheduleLine]:
    borders = _time_block_border_after_indices(times, teachers_source)
    lines: list[ScheduleLine] = []
    for index in range(len(times)):
        if not _schedule_line_has_content(
            times[index],
            teachers[index],
            responsible[index],
            rooms[index],
        ):
            continue
        lines.append(
            ScheduleLine(
                time=times[index],
                teacher=teachers[index],
                responsible=responsible[index],
                room=rooms[index],
                border_after=index in borders,
            )
        )
    return lines


def _format_teachers_preserve_lines(times: list[str], teachers: list[str]) -> list[str]:
    """Show full teacher roster on first line of a time block; leave empty if roster unchanged."""
    if not teachers:
        return []

    result = [""] * len(teachers)
    prev_roster: tuple[str, ...] | None = None

    for start, end in _schedule_blocks(times):
        block_values = [teachers[index] for index in range(start, end)]
        roster = _roster_key(block_values)
        if not roster:
            continue
        if roster == prev_roster:
            continue

        names = _roster_display_names(block_values)
        if names:
            result[start] = ", ".join(names)
        prev_roster = roster

    return result


def _align_schedule_lists(
    times: list[str],
    teachers: list[str],
    responsible: list[str],
    rooms: list[str],
) -> tuple[list[str], list[str], list[str], list[str]]:
    size = max(len(times), len(teachers), len(rooms), len(responsible))
    if size == 0:
        return [], [], [], []
    return (
        _pad_list(times, size),
        _pad_list(teachers, size),
        _pad_list(responsible, size),
        _pad_list(rooms, size),
    )


def _sort_aligned_schedule(
    times: list[str],
    teachers: list[str],
    responsible: list[str],
    rooms: list[str],
) -> tuple[list[str], list[str], list[str], list[str]]:
    times, teachers, responsible, rooms = _align_schedule_lists(
        times, teachers, responsible, rooms
    )
    size = len(times)
    if size <= 1:
        return times, teachers, responsible, rooms

    order = sorted(
        range(size),
        key=lambda index: (_time_sort_key(times[index]) if times[index] else (99, 99), index),
    )
    return (
        [times[index] for index in order],
        [teachers[index] for index in order],
        [responsible[index] for index in order],
        [rooms[index] for index in order],
    )


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return _normalize(row[index])


def _is_header_row(row: list[str]) -> bool:
    joined = " ".join(cell.casefold() for cell in row)
    hits = sum(
        1
        for aliases in COLUMN_ALIASES.values()
        for alias in aliases
        if alias in joined
    )
    return hits >= 2


def _detect_columns_from_header(header: list[str]) -> ColumnMapping:
    mapping = ColumnMapping()
    for index, cell in enumerate(header):
        text = _normalize(cell).casefold()
        if mapping.group is None and any(alias in text for alias in COLUMN_ALIASES["group"]):
            mapping.group = index
        elif mapping.time is None and any(alias in text for alias in COLUMN_ALIASES["time"]):
            mapping.time = index
        elif mapping.teacher is None and any(alias in text for alias in COLUMN_ALIASES["teacher"]):
            mapping.teacher = index
        elif mapping.responsible is None and any(
            alias in text for alias in COLUMN_ALIASES["responsible"]
        ):
            mapping.responsible = index
        elif mapping.room is None and any(alias in text for alias in COLUMN_ALIASES["room"]):
            mapping.room = index
        elif mapping.group_prefix is None and any(
            alias in text for alias in COLUMN_ALIASES["prefix"]
        ):
            mapping.group_prefix = index
    return mapping


def _score_columns(rows: list[list[str]]) -> dict[int, dict[str, float]]:
    scores: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    sample = rows[: min(30, len(rows))]

    for row in sample:
        for index, cell in enumerate(row):
            text = _normalize(cell)
            if not text:
                continue

            time_ranges = TIME_RANGE_PATTERN.findall(text)
            if time_ranges:
                scores[index]["time"] += len(time_ranges) * 5

            if _is_spurious_time(text) or (
                TIME_SINGLE_PATTERN.match(text) and len(time_ranges) == 0
            ):
                scores[index]["excel_time"] += 2

            if GROUP_PREFIX_PATTERN.match(text):
                scores[index]["prefix"] += 5

            if GROUP_FULL_PATTERN.match(text) and len(text) > 6:
                scores[index]["group_text"] += 4

            if PERSON_PATTERN.search(text):
                scores[index]["person"] += 4

            for part in _split_values(text):
                if THREE_DIGIT_PATTERN.match(part):
                    scores[index]["three_digit"] += 1
                if ID_NUMBER_PATTERN.match(part) and len(part) >= 4:
                    scores[index]["id_number"] += 2

    return scores


def _best_column(scores: dict[int, dict[str, float]], key: str, exclude: set[int]) -> int | None:
    candidates = [
        (index, metrics.get(key, 0))
        for index, metrics in scores.items()
        if index not in exclude and metrics.get(key, 0) > 0
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[1], reverse=True)
    return candidates[0][0]


def _infer_column_mapping(rows: list[list[str]], header: list[str] | None) -> ColumnMapping:
    scores = _score_columns(rows)
    mapping = ColumnMapping()

    if header:
        mapping = _detect_columns_from_header(header)
        if mapping.group is not None:
            mapping.skip.add(mapping.group)

    mapping.time = mapping.time if mapping.time is not None else _best_column(scores, "time", mapping.skip)
    if mapping.time is not None:
        mapping.skip.add(mapping.time)

    excel_time_col = _best_column(scores, "excel_time", mapping.skip)
    if excel_time_col is not None:
        mapping.skip.add(excel_time_col)

    mapping.group = mapping.group if mapping.group is not None else _best_column(
        scores, "group_text", mapping.skip
    )
    if mapping.group is not None:
        mapping.skip.add(mapping.group)

    mapping.group_prefix = (
        mapping.group_prefix
        if mapping.group_prefix is not None
        else _best_column(scores, "prefix", mapping.skip)
    )
    if mapping.group_prefix is not None:
        mapping.skip.add(mapping.group_prefix)

    mapping.teacher = mapping.teacher if mapping.teacher is not None else _best_column(
        scores, "person", mapping.skip
    )
    if mapping.teacher is None:
        mapping.teacher = _best_column(scores, "id_number", mapping.skip)
    if mapping.teacher is not None:
        mapping.skip.add(mapping.teacher)

    mapping.responsible = (
        mapping.responsible
        if mapping.responsible is not None
        else _best_column(scores, "person", mapping.skip)
    )
    if mapping.responsible is not None and mapping.responsible == mapping.teacher:
        mapping.responsible = _best_column(
            scores,
            "person",
            mapping.skip | {mapping.teacher},
        )
    if mapping.responsible is not None:
        mapping.skip.add(mapping.responsible)

    three_digit_cols = sorted(
        [
            index
            for index, metrics in scores.items()
            if index not in mapping.skip and metrics.get("three_digit", 0) > 0
        ],
        key=lambda index: scores[index]["three_digit"],
        reverse=True,
    )

    if mapping.room is None and mapping.group_prefix is not None and three_digit_cols:
        mapping.group_number = three_digit_cols[0]
        mapping.skip.add(mapping.group_number)
        if len(three_digit_cols) > 1:
            mapping.room = three_digit_cols[1]
            mapping.skip.add(mapping.room)
    else:
        if mapping.room is None and three_digit_cols:
            mapping.room = three_digit_cols[0]
            mapping.skip.add(mapping.room)
        if mapping.group is None and len(three_digit_cols) > 1:
            candidate = next(
                (index for index in three_digit_cols if index not in mapping.skip),
                None,
            )
            if candidate is not None:
                mapping.group_number = candidate
                mapping.skip.add(mapping.group_number)

    return mapping


def _apply_fixed_columns(mapping: ColumnMapping, selected: SelectedRange) -> ColumnMapping:
    room_index = selected.column_index_in_selection(ROOM_COL)
    if room_index is not None:
        mapping.room = room_index
        mapping.skip.add(room_index)

    teacher_index = selected.column_index_in_selection(TEACHER_COL)
    if teacher_index is not None:
        mapping.teacher = teacher_index
        mapping.skip.add(teacher_index)

    students_index = selected.column_index_in_selection(STUDENTS_COL)
    program_index = selected.column_index_in_selection(PROGRAM_NUMBER_COL)
    program_mid_index = selected.column_index_in_selection(PROGRAM_MID_COL)
    program_alt_index = selected.column_index_in_selection(PROGRAM_ALT_COL)
    if (
        students_index is not None
        or program_index is not None
        or program_mid_index is not None
        or program_alt_index is not None
    ):
        mapping.group = None
        mapping.group_prefix = None
        mapping.group_number = None
        mapping.group_students = students_index
        mapping.group_program = program_index
        mapping.group_program_mid = program_mid_index
        mapping.group_program_alt = program_alt_index
        if students_index is not None:
            mapping.skip.add(students_index)
        if program_index is not None:
            mapping.skip.add(program_index)
        if program_mid_index is not None:
            mapping.skip.add(program_mid_index)
        if program_alt_index is not None:
            mapping.skip.add(program_alt_index)

    return mapping


def _program_number(row: list[str], mapping: ColumnMapping) -> str:
    return _cell(row, mapping.group_program)


def _program_match_suffix(row: list[str], mapping: ColumnMapping) -> str:
    program = _program_number(row, mapping)
    if program:
        return program
    alt = _cell(row, mapping.group_program_alt)
    mid = _cell(row, mapping.group_program_mid)
    if alt:
        if mid and mid.strip().casefold() == "и":
            return f"и{alt.strip()}"
        return alt
    return mid


def _compose_group_label(students: str, program: str) -> str:
    if students and program:
        students = students.strip()
        program = program.strip()
        if program.startswith("и") and students.upper().endswith("РЦПА"):
            suffix = program[1:].lstrip() if program[1:2].isspace() else program[1:]
            return f"{students}и{suffix}"
        return f"{students} {program}"
    return students or program


def _build_group_key(
    row: list[str],
    mapping: ColumnMapping,
    last_match_key: str,
    last_display_name: str,
    last_students: str,
    last_program: str,
) -> tuple[str, str, str, str]:
    explicit = _explicit_group_key(row, mapping, last_students, last_program)
    if explicit is not None:
        return explicit
    if last_match_key and _row_is_continuation(row, mapping):
        return last_match_key, last_display_name, last_students, last_program
    if mapping.group_program is not None and not _program_match_suffix(row, mapping):
        return "", "", last_students, last_program
    return "", "", last_students, last_program


def _explicit_group_key(
    row: list[str],
    mapping: ColumnMapping,
    last_students: str = "",
    last_program: str = "",
) -> tuple[str, str, str, str] | None:
    if (
        mapping.group_students is not None
        or mapping.group_program is not None
        or mapping.group_program_mid is not None
        or mapping.group_program_alt is not None
    ):
        students_cell = _cell(row, mapping.group_students)
        students = students_cell or last_students
        match_suffix = _program_match_suffix(row, mapping)
        display_name = _compose_group_label(students, _program_number(row, mapping))
        match_key = _compose_group_label(students, match_suffix)
        if match_key:
            if students_cell:
                last_students = students_cell
            if match_suffix:
                last_program = match_suffix
            return match_key, display_name, last_students, last_program
        return None

    if mapping.group is not None:
        group = _cell(row, mapping.group)
        if group:
            return group, group, last_students, last_program
        return None

    prefix = _cell(row, mapping.group_prefix)
    number = _cell(row, mapping.group_number)

    if prefix and number:
        label = f"{prefix} {number}"
        return label, label, last_students, last_program
    if prefix:
        return prefix, prefix, last_students, last_program
    if number:
        return number, number, last_students, last_program
    return None


def _row_is_continuation(row: list[str], mapping: ColumnMapping) -> bool:
    return bool(
        _extract_times(_cell(row, mapping.time))
        or _split_values(_cell(row, mapping.teacher))
        or _split_values(_cell(row, mapping.responsible))
        or _extract_rooms(_cell(row, mapping.room))
    )


def aggregate_by_groups(
    selected: SelectedRange,
    responsible_mappings: list[ResponsibleEntry] | None = None,
) -> list[GroupAggregate]:
    rows = _pad_rows([[_normalize(cell) for cell in row] for row in selected.data])
    rows = [row for row in rows if any(cell for cell in row)]
    if not rows:
        return []

    start_index = 0
    header: list[str] | None = None
    if _is_header_row(rows[0]):
        header = rows[0]
        start_index = 1

    data_rows = rows[start_index:]
    if not data_rows:
        return []

    mapping = _apply_fixed_columns(_infer_column_mapping(data_rows, header), selected)
    grouped: OrderedDict[str, dict[str, list[str]]] = OrderedDict()
    last_match_key = ""
    last_display_name = ""
    last_students = ""
    last_program = ""

    for row in data_rows:
        if not _is_meaningful_row(row, mapping):
            continue

        match_key, display_name, last_students, last_program = _build_group_key(
            row,
            mapping,
            last_match_key,
            last_display_name,
            last_students,
            last_program,
        )
        if not match_key:
            continue
        last_match_key = match_key
        last_display_name = display_name

        if match_key not in grouped:
            grouped[match_key] = {
                "name": display_name,
                "times": [],
                "teachers": [],
                "responsible": [],
                "rooms": [],
            }

        bucket = grouped[match_key]
        times, teachers, _, rooms = _aligned_schedule_from_row(row, mapping)
        _append_schedule_to_bucket(bucket, times, teachers, rooms)

    sorted_groups = sorted(
        grouped.items(),
        key=lambda item: _earliest_time_key(item[1]["times"]),
    )

    room_index = build_room_index(responsible_mappings or [])

    result: list[GroupAggregate] = []
    for index, (match_key, bucket) in enumerate(sorted_groups, start=1):
        times, teachers, _, rooms = _sort_aligned_schedule(
            bucket["times"],
            bucket["teachers"],
            bucket["responsible"],
            bucket["rooms"],
        )
        times = _dedupe_preserve_lines(times)
        teachers_source = list(teachers)
        (
            times,
            teachers,
            _,
            rooms,
            teachers_source,
        ) = _compact_schedule_rows(times, teachers, rooms, teachers_source)
        teachers = _format_teachers_preserve_lines(times, teachers)
        if room_index:
            responsible = format_responsible_lines(
                times,
                resolve_responsible_lines(rooms, room_index),
            )
        else:
            responsible = [""] * len(times)
        (
            times,
            teachers,
            responsible,
            rooms,
            teachers_source,
        ) = _compact_schedule_rows(
            times,
            teachers,
            rooms,
            teachers_source,
            responsible,
        )
        lines = _build_schedule_lines(
            times,
            teachers,
            responsible,
            rooms,
            teachers_source,
        )
        if not lines:
            continue
        result.append(
            GroupAggregate(
                index=index,
                group=bucket["name"] or match_key,
                lines=lines,
            )
        )
    return result
