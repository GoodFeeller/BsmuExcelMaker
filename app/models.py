from dataclasses import dataclass, field


def column_index_to_letter(col: int) -> str:
    """Convert 1-based column index to Excel letter notation (1 -> A, 27 -> AA)."""
    result = ""
    while col > 0:
        col, remainder = divmod(col - 1, 26)
        result = chr(65 + remainder) + result
    return result


def column_letter_to_index(col: str) -> int:
    """Convert Excel column letter to 1-based index (A -> 1, F -> 6)."""
    index = 0
    for char in col.upper():
        index = index * 26 + (ord(char) - 64)
    return index


PROGRAM_NUMBER_COL = column_letter_to_index("F")
PROGRAM_ALT_COL = column_letter_to_index("G")
STUDENTS_COL = column_letter_to_index("E")
ROOM_COL = column_letter_to_index("B")
TEACHER_COL = column_letter_to_index("J")


@dataclass
class SelectedRange:
    sheet_name: str
    top_row: int
    left_col: int
    bottom_row: int
    right_col: int
    data: list[list]

    @property
    def address(self) -> str:
        start = f"{column_index_to_letter(self.left_col)}{self.top_row}"
        end = f"{column_index_to_letter(self.right_col)}{self.bottom_row}"
        if start == end:
            return start
        return f"{start}:{end}"

    @property
    def row_count(self) -> int:
        return self.bottom_row - self.top_row + 1

    @property
    def col_count(self) -> int:
        return self.right_col - self.left_col + 1

    @property
    def cell_count(self) -> int:
        return self.row_count * self.col_count

    def column_index_in_selection(self, excel_col: int) -> int | None:
        if excel_col < self.left_col or excel_col > self.right_col:
            return None
        return excel_col - self.left_col

@dataclass
class GroupAggregate:
    index: int
    group: str
    times: list[str] = field(default_factory=list)
    teachers: list[str] = field(default_factory=list)
    responsible: list[str] = field(default_factory=list)
    rooms: list[str] = field(default_factory=list)

    @property
    def times_text(self) -> str:
        return "\n".join(self.times)

    @property
    def teachers_text(self) -> str:
        return ",\n".join(self.teachers)

    @property
    def responsible_text(self) -> str:
        return "\n".join(self.responsible)

    @property
    def rooms_text(self) -> str:
        return "\n".join(self.rooms)
