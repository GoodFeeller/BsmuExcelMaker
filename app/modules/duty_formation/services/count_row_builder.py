from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.cell_utils import format_cell, normalize_cell
from app.modules.duty_formation.models import (
    DATE_COL,
    PLAN_COL,
    PROGRAM_ALT_COL,
    PROGRAM_MID_COL,
    PROGRAM_NUMBER_COL,
    ROOM_COL,
    STUDENTS_COL,
    TEACHER_COL,
    SelectedRange,
)
from app.modules.duty_formation.services.schedule_aggregator import (
    ColumnMapping,
    _best_column,
    _cell,
    _is_header_row,
    _is_meaningful_row,
    _score_columns,
)

COUNT_DATA_COLUMNS = 19


def _frame_row(frame: pd.DataFrame, row_idx: int) -> list[str]:
    return [normalize_cell(frame.iat[row_idx, col]) for col in range(frame.shape[1])]


def _parse_report_datetime(report_date: str) -> datetime:
    parsed = datetime.strptime(report_date, "%d.%m.%Y")
    return parsed.replace(hour=0, minute=0, second=0, microsecond=0)


def _parse_plan_value(text: str):
    text = normalize_cell(text)
    if not text:
        return None
    try:
        if "." in text:
            value = float(text.replace(",", "."))
            if value.is_integer():
                return int(value)
            return value
        return int(text)
    except ValueError:
        return text


def _detect_plan_column(frame: pd.DataFrame) -> int | None:
    for row_idx in range(min(5, len(frame))):
        for col_idx in range(frame.shape[1]):
            label = normalize_cell(frame.iat[row_idx, col_idx]).casefold()
            if label == "план" or label.startswith("план "):
                return col_idx
    if frame.shape[1] >= PLAN_COL:
        return PLAN_COL - 1
    return None


def build_absolute_mapping(
    frame: pd.DataFrame,
    row_indices: list[int],
) -> ColumnMapping:
    mapping = ColumnMapping()
    ncol = frame.shape[1]

    def assign(attr: str, excel_col: int) -> None:
        index = excel_col - 1
        if index < ncol:
            setattr(mapping, attr, index)
            mapping.skip.add(index)

    assign("room", ROOM_COL)
    assign("group_students", STUDENTS_COL)
    assign("group_program", PROGRAM_NUMBER_COL)
    assign("group_program_mid", PROGRAM_MID_COL)
    assign("group_program_alt", PROGRAM_ALT_COL)
    assign("teacher", TEACHER_COL)

    sample = [_frame_row(frame, index) for index in row_indices[:30]]
    if sample:
        scores = _score_columns(sample)
        exclude = set(mapping.skip)
        mapping.time = _best_column(scores, "time", exclude) or _best_column(
            scores, "excel_time", exclude
        )

    return mapping


def _selection_row_indices(
    frame: pd.DataFrame,
    selected: SelectedRange,
) -> list[int]:
    start = max(0, selected.top_row - 1)
    end = min(len(frame) - 1, selected.bottom_row - 1)
    indices = list(range(start, end + 1))
    if indices and _is_header_row(_frame_row(frame, indices[0])):
        indices = indices[1:]
    return indices


def build_count_rows(
    frame: pd.DataFrame,
    selected: SelectedRange,
    report_date: str,
) -> list[list]:
    if frame.empty or not selected:
        return []

    row_indices = _selection_row_indices(frame, selected)
    if not row_indices:
        return []

    mapping = build_absolute_mapping(frame, row_indices)
    plan_col = _detect_plan_column(frame)
    report_dt = _parse_report_datetime(report_date)

    rows: list[list] = []
    for row_idx in row_indices:
        row = _frame_row(frame, row_idx)
        if not _is_meaningful_row(row, mapping):
            continue

        room = _cell(row, mapping.room)
        time_value = _cell(row, mapping.time)
        students = _cell(row, mapping.group_students)
        program_number = _cell(row, mapping.group_program)
        program_name = _cell(row, mapping.group_program_mid)
        department = _cell(row, mapping.group_program_alt)
        teachers = _cell(row, mapping.teacher)

        plan_value = None
        if plan_col is not None and plan_col < len(row):
            plan_value = _parse_plan_value(row[plan_col])

        date_value = report_dt
        if DATE_COL - 1 < len(row):
            raw_date = frame.iat[row_idx, DATE_COL - 1]
            if raw_date is not None and normalize_cell(raw_date):
                if isinstance(raw_date, datetime):
                    date_value = raw_date.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                else:
                    parsed = datetime.strptime(report_date, "%d.%m.%Y")
                    date_value = parsed

        rows.append(
            [
                _parse_room_number(room),
                date_value,
                time_value,
                students,
                _parse_program_number(program_number),
                program_name,
                department,
                plan_value,
                teachers,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ]
        )

    return rows


def _parse_room_number(room: str):
    text = normalize_cell(room)
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if digits:
        try:
            return int(digits)
        except ValueError:
            pass
    return text


def _parse_program_number(value: str):
    text = normalize_cell(value)
    if not text:
        return None
    try:
        if text.isdigit():
            return int(text)
        value_float = float(text.replace(",", "."))
        if value_float.is_integer():
            return int(value_float)
        return value_float
    except ValueError:
        return text
