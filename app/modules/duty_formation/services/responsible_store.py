import json
from datetime import date
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from app.modules.duty_formation.services.responsible_mapping import (
    ResponsibleEntry,
    parse_rooms_text,
)

JSON_VERSION = 1
CACHE_FILE_NAME = "app_settings.json"
LEGACY_CACHE_FILE_NAME = "responsible_specialists.json"


def _settings_dir() -> Path:
    base = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
    if not base.name:
        base = Path.home() / ".bsmu_excel_worker"
    directory = base / "RCPCSTSheduler"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _cache_path() -> Path:
    return _settings_dir() / CACHE_FILE_NAME


def _legacy_cache_path() -> Path:
    return _settings_dir() / LEGACY_CACHE_FILE_NAME


def default_report_date() -> str:
    return date.today().strftime("%d.%m.%Y")


def entries_to_data(
    entries: list[ResponsibleEntry],
    report_date: str | None = None,
    duty_specialist: str | None = None,
) -> dict:
    payload = {
        "version": JSON_VERSION,
        "entries": [
            {"name": entry.name, "rooms": list(entry.rooms)}
            for entry in entries
        ],
    }
    if report_date:
        payload["report_date"] = report_date
    if duty_specialist:
        payload["duty_specialist"] = duty_specialist
    return payload


def entries_from_data(data: dict) -> list[ResponsibleEntry]:
    if not isinstance(data, dict):
        raise ValueError("Некорректный формат JSON")

    raw_entries = data.get("entries", data if isinstance(data, list) else None)
    if not isinstance(raw_entries, list):
        raise ValueError("В JSON отсутствует список entries")

    entries: list[ResponsibleEntry] = []
    for item in raw_entries:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        rooms_raw = item.get("rooms", [])
        if isinstance(rooms_raw, str):
            rooms = parse_rooms_text(rooms_raw)
        elif isinstance(rooms_raw, list):
            rooms = []
            for room in rooms_raw:
                rooms.extend(parse_rooms_text(str(room)))
            seen: set[str] = set()
            unique_rooms: list[str] = []
            for room in rooms:
                if room not in seen:
                    seen.add(room)
                    unique_rooms.append(room)
            rooms = unique_rooms
        else:
            rooms = []
        if name and rooms:
            entries.append(ResponsibleEntry(name=name, rooms=rooms))
    return entries


def _read_settings_file() -> dict | None:
    legacy_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
    legacy_paths = [
        _cache_path(),
        _legacy_cache_path(),
        legacy_dir / "BsmuExcelWorker" / CACHE_FILE_NAME,
        legacy_dir / "BsmuExcelWorker" / LEGACY_CACHE_FILE_NAME,
    ]
    for path in legacy_paths:
        if not path.exists():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    return None


def load_settings() -> tuple[list[ResponsibleEntry], str, str]:
    data = _read_settings_file()
    if not data:
        return [], default_report_date(), ""
    try:
        entries = entries_from_data(data)
    except ValueError:
        entries = []
    report_date = str(data.get("report_date", "")).strip() or default_report_date()
    duty_specialist = str(data.get("duty_specialist", "")).strip()
    return entries, report_date, duty_specialist


def specialist_names(entries: list[ResponsibleEntry]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        key = entry.name.casefold()
        if entry.name and key not in seen:
            seen.add(key)
            names.append(entry.name)
    return names


def load_cache() -> list[ResponsibleEntry]:
    entries, _, _ = load_settings()
    return entries


def save_settings(
    entries: list[ResponsibleEntry],
    report_date: str,
    duty_specialist: str = "",
) -> None:
    path = _cache_path()
    path.write_text(
        json.dumps(
            entries_to_data(
                entries,
                report_date=report_date,
                duty_specialist=duty_specialist,
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def save_cache(
    entries: list[ResponsibleEntry],
    report_date: str | None = None,
    duty_specialist: str = "",
) -> None:
    save_settings(
        entries,
        report_date or default_report_date(),
        duty_specialist=duty_specialist,
    )


def export_to_json_file(entries: list[ResponsibleEntry], path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(entries_to_data(entries), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def import_from_json_file(path: str | Path) -> list[ResponsibleEntry]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return entries_from_data(data)
