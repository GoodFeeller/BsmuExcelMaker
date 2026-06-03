from pathlib import Path
import warnings

import pandas as pd

from app.cell_utils import normalize_cell

SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}


def _engine_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        return "openpyxl"
    if suffix == ".xls":
        return "xlrd"
    raise ValueError(f"Неподдерживаемый формат файла: {suffix}")


def trim_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove trailing empty rows and columns to avoid rendering huge sparse grids."""
    if frame.empty:
        return frame

    mask = frame.map(lambda value: bool(normalize_cell(value)))
    row_mask = mask.any(axis=1)
    col_mask = mask.any(axis=0)
    if not row_mask.any() or not col_mask.any():
        return frame.iloc[0:0, 0:0].copy()

    row_indices = row_mask[row_mask].index
    col_indices = col_mask[col_mask].index
    trimmed = frame.loc[row_indices[0] : row_indices[-1], col_indices[0] : col_indices[-1]]
    return trimmed.reset_index(drop=True)


def load_workbook(path: str | Path) -> dict[str, pd.DataFrame]:
    file_path = Path(path)
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Поддерживаются только файлы {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    engine = _engine_for_path(file_path)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Data Validation extension is not supported and will be removed",
            category=UserWarning,
        )
        sheets = pd.read_excel(
            file_path,
            sheet_name=None,
            header=None,
            engine=engine,
        )

    result: dict[str, pd.DataFrame] = {}
    for sheet_name, frame in sheets.items():
        cleaned = frame.fillna("")
        result[str(sheet_name)] = trim_dataframe(cleaned)
    return result
