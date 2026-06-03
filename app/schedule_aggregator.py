import re
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

from app.cell_utils import normalize_cell
from app.models import (
    GroupAggregate,
    PROGRAM_ALT_COL,
    PROGRAM_NUMBER_COL,
    ROOM_COL,
    STUDENTS_COL,
    TEACHER_COL,
    SelectedRange,
)

TIME_RANGE_PATTERN = re.compile(
    r"\d{1,2}[.:]\d{2}\s*[–\-—−]\s*\d{1,2}[.:]\d{2}",
    re.IGNORECASE,
)
TIME_SINGLE_PATTERN = re.compile(r"^\d{1,2}[.:]\d{2}$")
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

    identity, _, _ = _explicit_group_key(row, mapping)
    return bool(identity)


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
    program_alt_index = selected.column_index_in_selection(PROGRAM_ALT_COL)
    if (
        students_index is not None
        or program_index is not None
        or program_alt_index is not None
    ):
        mapping.group = None
        mapping.group_prefix = None
        mapping.group_number = None
        mapping.group_students = students_index
        mapping.group_program = program_index
        mapping.group_program_alt = program_alt_index
        if students_index is not None:
            mapping.skip.add(students_index)
        if program_index is not None:
            mapping.skip.add(program_index)
        if program_alt_index is not None:
            mapping.skip.add(program_alt_index)

    return mapping


def _program_suffix(row: list[str], mapping: ColumnMapping) -> str:
    program = _cell(row, mapping.group_program)
    if program:
        return program
    return _cell(row, mapping.group_program_alt)


def _compose_group_label(students: str, program: str) -> str:
    if students and program:
        return f"{students} {program}"
    return students or program


def _build_group_key(
    row: list[str],
    mapping: ColumnMapping,
    last_group: str,
    last_students: str,
    last_program: str,
) -> tuple[str, str, str]:
    explicit, students, program = _explicit_group_key(row, mapping, last_students, last_program)
    if explicit:
        return explicit, students, program
    if mapping.group_program is not None and not _program_suffix(row, mapping):
        return "", last_students, last_program
    if last_group and _row_is_continuation(row, mapping):
        return last_group, last_students, last_program
    return "", last_students, last_program


def _explicit_group_key(
    row: list[str],
    mapping: ColumnMapping,
    last_students: str = "",
    last_program: str = "",
) -> tuple[str, str, str]:
    if (
        mapping.group_students is not None
        or mapping.group_program is not None
        or mapping.group_program_alt is not None
    ):
        students_cell = _cell(row, mapping.group_students)
        program_cell = _program_suffix(row, mapping)
        students = students_cell or last_students
        program = program_cell
        label = _compose_group_label(students, program)
        if label:
            if students_cell:
                last_students = students_cell
            if program_cell:
                last_program = program_cell
            return label, last_students, last_program
        return "", last_students, last_program

    if mapping.group is not None:
        group = _cell(row, mapping.group)
        if group:
            return group, last_students, last_program
        return "", last_students, last_program

    prefix = _cell(row, mapping.group_prefix)
    number = _cell(row, mapping.group_number)

    if prefix and number:
        return f"{prefix} {number}", last_students, last_program
    if prefix:
        return prefix, last_students, last_program
    if number:
        return number, last_students, last_program
    return "", last_students, last_program


def _row_is_continuation(row: list[str], mapping: ColumnMapping) -> bool:
    return bool(
        _extract_times(_cell(row, mapping.time))
        or _split_values(_cell(row, mapping.teacher))
        or _split_values(_cell(row, mapping.responsible))
        or _extract_rooms(_cell(row, mapping.room))
    )


def aggregate_by_groups(selected: SelectedRange) -> list[GroupAggregate]:
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
    last_group = ""
    last_students = ""
    last_program = ""

    for row in data_rows:
        if not _is_meaningful_row(row, mapping):
            continue

        group, last_students, last_program = _build_group_key(
            row, mapping, last_group, last_students, last_program
        )
        if not group:
            continue
        last_group = group

        if group not in grouped:
            grouped[group] = {
                "times": [],
                "teachers": [],
                "responsible": [],
                "rooms": [],
            }

        bucket = grouped[group]
        bucket["times"].extend(_extract_times(_cell(row, mapping.time)))
        bucket["teachers"].extend(_split_values(_cell(row, mapping.teacher)))
        bucket["responsible"].extend(_split_values(_cell(row, mapping.responsible)))
        bucket["rooms"].extend(_extract_rooms(_cell(row, mapping.room)))

    result: list[GroupAggregate] = []
    for index, (group, bucket) in enumerate(grouped.items(), start=1):
        result.append(
            GroupAggregate(
                index=index,
                group=group,
                times=_unique_preserve(bucket["times"]),
                teachers=_unique_preserve(bucket["teachers"]),
                responsible=_unique_preserve(bucket["responsible"]),
                rooms=_unique_preserve(bucket["rooms"]),
            )
        )
    return result
