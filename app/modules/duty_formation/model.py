from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from app.modules.duty_formation.models import GroupAggregate, SelectedRange
from app.modules.duty_formation.services.responsible_store import default_report_date


@dataclass
class DutyFormationModel:
    current_file: Path | None = None
    selected_range: SelectedRange | None = None
    aggregated_groups: list[GroupAggregate] = field(default_factory=list)
    sheets: dict[str, pd.DataFrame] = field(default_factory=dict)
    report_date: str = field(default_factory=default_report_date)
    duty_specialist: str = ""

    def clear_workbook(self) -> None:
        self.current_file = None
        self.selected_range = None
        self.aggregated_groups = []
        self.sheets = {}
