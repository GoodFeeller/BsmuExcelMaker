from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CountSummaryStats:
    report_date: str
    groups_count: int
    visits_count: int
    plan_total: int | float | None
    fact_total: int | float | None
    cushion_total: int | float | None
    ko: int | float | None = None
    i_cat: int | float | None = None
    pk: int | float | None = None
    pp: int | float | None = None
    attestation: int | float | None = None
    bgmu: int | float | None = None
    mfiu: int | float | None = None
    other: str | int | float | None = None
    source_path: str = ""

    @property
    def category_values(self) -> list[str | int | float | None]:
        return [
            self.ko,
            self.i_cat,
            self.pk,
            self.pp,
            self.attestation,
            self.bgmu,
            self.mfiu,
            self.other,
        ]


@dataclass
class DutySummaryModel:
    report_date: str = ""
    duty_specialist: str = ""
    current_file: str | None = None
    stats: CountSummaryStats | None = None
